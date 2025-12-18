"""
Tenant-Aware NLP2SQL Engine
Enhanced NLP2SQL engine with tenant-specific schema awareness and data isolation.
"""

import json
import logging
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import create_engine, text, inspect, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from .tenant_connection_manager import TenantConnectionManager, DatabaseType
from .tenant_routing_middleware import TenantRoutingContext
from .nlp2sql_engine import NLP2SQLEngine  # Original engine


logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Types of NLP queries."""
    SELECT = "SELECT"
    AGGREGATE = "AGGREGATE"
    JOIN = "JOIN"
    FILTER = "FILTER"
    GROUPBY = "GROUPBY"
    ORDERBY = "ORDERBY"
    COMPLEX = "COMPLEX"


class SecurityLevel(Enum):
    """Query security levels."""
    SAFE = "SAFE"
    RESTRICTED = "RESTRICTED"
    ADMIN_ONLY = "ADMIN_ONLY"
    FORBIDDEN = "FORBIDDEN"


@dataclass
class TenantSchemaInfo:
    """Tenant-specific database schema information."""
    tenant_id: str
    database_type: DatabaseType
    tables: Dict[str, Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    constraints: Dict[str, List[str]]
    indexes: Dict[str, List[str]]
    views: Dict[str, str]
    last_updated: datetime
    schema_version: str


@dataclass
class QueryAnalysis:
    """Analysis of a natural language query."""
    original_query: str
    query_type: QueryType
    tables_involved: List[str]
    columns_involved: List[str]
    security_level: SecurityLevel
    estimated_complexity: int
    requires_joins: bool
    has_aggregations: bool
    filter_conditions: List[str]
    confidence_score: float


@dataclass
class QueryResult:
    """Result of a tenant-aware query execution."""
    query_id: str
    tenant_id: str
    user_id: str
    original_query: str
    generated_sql: str
    execution_time_ms: float
    row_count: int
    data: List[Dict[str, Any]]
    security_filtered: bool
    cached: bool
    analysis: QueryAnalysis
    metadata: Dict[str, Any]


class TenantSchemaManager:
    """Manages tenant-specific database schemas and metadata."""

    def __init__(self, connection_manager: TenantConnectionManager):
        self.connection_manager = connection_manager
        self.schema_cache: Dict[str, TenantSchemaInfo] = {}
        self.cache_lock = threading.RLock()
        self.cache_ttl = 3600  # 1 hour

    def get_tenant_schema(self, tenant_id: str, force_refresh: bool = False) -> Optional[TenantSchemaInfo]:
        """Get tenant database schema information."""
        try:
            with self.cache_lock:
                # Check cache first
                if not force_refresh and tenant_id in self.schema_cache:
                    schema_info = self.schema_cache[tenant_id]
                    age = (datetime.utcnow() - schema_info.last_updated).seconds
                    if age < self.cache_ttl:
                        return schema_info

                # Refresh schema from database
                schema_info = self._extract_schema_info(tenant_id)
                if schema_info:
                    self.schema_cache[tenant_id] = schema_info

                return schema_info

        except Exception as e:
            logger.error(f"Error getting tenant schema for {tenant_id}: {e}")
            return None

    def _extract_schema_info(self, tenant_id: str) -> Optional[TenantSchemaInfo]:
        """Extract schema information from tenant database."""
        try:
            with self.connection_manager.get_connection_context(tenant_id) as connection:
                # Get tenant info to determine database type
                tenant_info = self.connection_manager.get_tenant_info(tenant_id)
                if not tenant_info:
                    return None

                database_type = tenant_info.database_type

                if database_type in [DatabaseType.MYSQL, DatabaseType.POSTGRESQL]:
                    return self._extract_sql_schema(tenant_id, connection, database_type)
                elif database_type == DatabaseType.SQLITE:
                    return self._extract_sqlite_schema(tenant_id, connection)
                elif database_type == DatabaseType.MONGODB:
                    return self._extract_mongodb_schema(tenant_id, connection)
                else:
                    logger.error(f"Unsupported database type: {database_type}")
                    return None

        except Exception as e:
            logger.error(f"Error extracting schema for tenant {tenant_id}: {e}")
            return None

    def _extract_sql_schema(self, tenant_id: str, connection, database_type: DatabaseType) -> TenantSchemaInfo:
        """Extract schema from SQL databases (MySQL/PostgreSQL)."""
        inspector = inspect(connection)

        # Get tables and columns
        tables = {}
        for table_name in inspector.get_table_names():
            columns = {}
            for column in inspector.get_columns(table_name):
                columns[column['name']] = {
                    'type': str(column['type']),
                    'nullable': column['nullable'],
                    'default': column.get('default'),
                    'primary_key': column.get('primary_key', False)
                }

            tables[table_name] = {
                'columns': columns,
                'primary_keys': [col['name'] for col in inspector.get_pk_constraint(table_name)['constrained_columns']],
                'foreign_keys': [
                    {
                        'column': fk['constrained_columns'][0],
                        'referenced_table': fk['referred_table'],
                        'referenced_column': fk['referred_columns'][0]
                    }
                    for fk in inspector.get_foreign_keys(table_name)
                ]
            }

        # Get relationships
        relationships = []
        for table_name, table_info in tables.items():
            for fk in table_info['foreign_keys']:
                relationships.append({
                    'from_table': table_name,
                    'from_column': fk['column'],
                    'to_table': fk['referenced_table'],
                    'to_column': fk['referenced_column'],
                    'type': 'foreign_key'
                })

        # Get indexes
        indexes = {}
        for table_name in tables.keys():
            table_indexes = []
            for index in inspector.get_indexes(table_name):
                table_indexes.append({
                    'name': index['name'],
                    'columns': index['column_names'],
                    'unique': index['unique']
                })
            indexes[table_name] = table_indexes

        # Get views
        views = {}
        try:
            for view_name in inspector.get_view_names():
                views[view_name] = f"VIEW: {view_name}"
        except Exception:
            pass  # Some databases don't support views

        return TenantSchemaInfo(
            tenant_id=tenant_id,
            database_type=database_type,
            tables=tables,
            relationships=relationships,
            constraints={},
            indexes=indexes,
            views=views,
            last_updated=datetime.utcnow(),
            schema_version="1.0"
        )

    def _extract_sqlite_schema(self, tenant_id: str, connection) -> TenantSchemaInfo:
        """Extract schema from SQLite database."""
        # SQLite schema extraction similar to SQL but with SQLite-specific queries
        inspector = inspect(connection)

        tables = {}
        for table_name in inspector.get_table_names():
            columns = {}
            for column in inspector.get_columns(table_name):
                columns[column['name']] = {
                    'type': str(column['type']),
                    'nullable': column['nullable'],
                    'default': column.get('default'),
                    'primary_key': column.get('primary_key', False)
                }

            tables[table_name] = {
                'columns': columns,
                'primary_keys': [],
                'foreign_keys': []
            }

        return TenantSchemaInfo(
            tenant_id=tenant_id,
            database_type=DatabaseType.SQLITE,
            tables=tables,
            relationships=[],
            constraints={},
            indexes={},
            views={},
            last_updated=datetime.utcnow(),
            schema_version="1.0"
        )

    def _extract_mongodb_schema(self, tenant_id: str, connection) -> TenantSchemaInfo:
        """Extract schema from MongoDB database."""
        # MongoDB schema extraction
        collections = {}

        try:
            for collection_name in connection.list_collection_names():
                # Sample documents to infer schema
                sample_docs = list(connection[collection_name].find().limit(100))

                if sample_docs:
                    # Infer schema from sample documents
                    fields = {}
                    for doc in sample_docs:
                        for field, value in doc.items():
                            if field not in fields:
                                fields[field] = {
                                    'type': type(value).__name__,
                                    'nullable': True,
                                    'examples': []
                                }
                            if len(fields[field]['examples']) < 5:
                                fields[field]['examples'].append(str(value)[:100])

                    collections[collection_name] = {
                        'fields': fields,
                        'document_count': connection[collection_name].count_documents({}),
                        'indexes': list(connection[collection_name].list_indexes())
                    }
        except Exception as e:
            logger.error(f"Error extracting MongoDB schema: {e}")

        return TenantSchemaInfo(
            tenant_id=tenant_id,
            database_type=DatabaseType.MONGODB,
            tables=collections,
            relationships=[],
            constraints={},
            indexes={},
            views={},
            last_updated=datetime.utcnow(),
            schema_version="1.0"
        )


class QuerySecurityAnalyzer:
    """Analyzes queries for security and access control."""

    def __init__(self):
        self.sensitive_patterns = [
            r'\bDROP\b', r'\bDELETE\b', r'\bTRUNCATE\b', r'\bALTER\b',
            r'\bCREATE\b', r'\bINSERT\b', r'\bUPDATE\b',
            r'\bGRANT\b', r'\bREVOKE\b', r'\bEXEC\b'
        ]

        self.admin_only_tables = [
            'users', 'user_permissions', 'system_settings', 'audit_logs'
        ]

    def analyze_query_security(self, query: str, tables_involved: List[str],
                             user_access_level: str) -> SecurityLevel:
        """Analyze query for security implications."""
        import re

        query_upper = query.upper()

        # Check for dangerous operations
        for pattern in self.sensitive_patterns:
            if re.search(pattern, query_upper):
                return SecurityLevel.FORBIDDEN

        # Check for admin-only table access
        for table in tables_involved:
            if table.lower() in self.admin_only_tables:
                if user_access_level not in ['ADMIN', 'SUPER_ADMIN']:
                    return SecurityLevel.ADMIN_ONLY

        # Check for potentially expensive operations
        if any(keyword in query_upper for keyword in ['JOIN', 'UNION', 'SUBQUERY']):
            if user_access_level == 'VIEWER':
                return SecurityLevel.RESTRICTED

        return SecurityLevel.SAFE

    def filter_query_results(self, results: List[Dict[str, Any]],
                           user_access_level: str,
                           tenant_context: TenantRoutingContext) -> Tuple[List[Dict[str, Any]], bool]:
        """Filter query results based on user access level."""
        if user_access_level in ['SUPER_ADMIN', 'ADMIN']:
            return results, False

        filtered_results = []
        filtered = False

        # Apply row-level security
        for row in results:
            filtered_row = {}

            for key, value in row.items():
                # Hide sensitive columns for non-admin users
                if self._is_sensitive_column(key) and user_access_level not in ['ADMIN', 'ANALYST']:
                    filtered_row[key] = '[HIDDEN]'
                    filtered = True
                else:
                    filtered_row[key] = value

            filtered_results.append(filtered_row)

        # Limit result size for certain user types
        if user_access_level == 'VIEWER' and len(filtered_results) > 100:
            filtered_results = filtered_results[:100]
            filtered = True

        return filtered_results, filtered

    def _is_sensitive_column(self, column_name: str) -> bool:
        """Check if a column contains sensitive data."""
        sensitive_keywords = [
            'password', 'secret', 'token', 'key', 'hash',
            'ssn', 'social_security', 'credit_card', 'phone',
            'email', 'personal', 'private'
        ]

        column_lower = column_name.lower()
        return any(keyword in column_lower for keyword in sensitive_keywords)


class TenantAwareNLP2SQL:
    """
    Enhanced NLP2SQL engine with tenant awareness and data isolation.
    """

    def __init__(self, connection_manager: TenantConnectionManager,
                 original_engine: NLP2SQLEngine = None):
        self.connection_manager = connection_manager
        self.original_engine = original_engine or NLP2SQLEngine()

        # Tenant-specific components
        self.schema_manager = TenantSchemaManager(connection_manager)
        self.security_analyzer = QuerySecurityAnalyzer()

        # Caching
        self.query_cache: Dict[str, QueryResult] = {}
        self.cache_lock = threading.RLock()
        self.cache_ttl = 300  # 5 minutes

        # Performance tracking
        self.performance_metrics = {}

    async def process_nlp_query(self, natural_query: str, tenant_context: TenantRoutingContext) -> QueryResult:
        """Process natural language query with tenant awareness."""
        query_id = self._generate_query_id(natural_query, tenant_context.tenant_id)
        start_time = time.time()

        try:
            # Check cache first
            cached_result = self._get_cached_result(query_id, tenant_context)
            if cached_result:
                return cached_result

            # Get tenant schema
            schema_info = self.schema_manager.get_tenant_schema(tenant_context.tenant_id)
            if not schema_info:
                raise Exception(f"Could not retrieve schema for tenant: {tenant_context.tenant_id}")

            # Analyze the natural language query
            analysis = await self._analyze_query(natural_query, schema_info, tenant_context)

            # Security check
            if analysis.security_level == SecurityLevel.FORBIDDEN:
                raise Exception("Query contains forbidden operations")

            if analysis.security_level == SecurityLevel.ADMIN_ONLY and tenant_context.access_level not in ['ADMIN', 'SUPER_ADMIN']:
                raise Exception("Query requires administrator privileges")

            # Generate SQL with tenant-specific context
            generated_sql = await self._generate_tenant_sql(natural_query, schema_info, analysis, tenant_context)

            # Execute query with tenant isolation
            execution_result = await self._execute_tenant_query(
                generated_sql, tenant_context, analysis
            )

            # Apply security filtering
            filtered_data, was_filtered = self.security_analyzer.filter_query_results(
                execution_result['data'],
                tenant_context.access_level,
                tenant_context
            )

            # Create result object
            result = QueryResult(
                query_id=query_id,
                tenant_id=tenant_context.tenant_id,
                user_id=tenant_context.user_id,
                original_query=natural_query,
                generated_sql=generated_sql,
                execution_time_ms=(time.time() - start_time) * 1000,
                row_count=len(filtered_data),
                data=filtered_data,
                security_filtered=was_filtered,
                cached=False,
                analysis=analysis,
                metadata={
                    'schema_version': schema_info.schema_version,
                    'database_type': schema_info.database_type.value,
                    'query_complexity': analysis.estimated_complexity,
                    'confidence_score': analysis.confidence_score
                }
            )

            # Cache result if appropriate
            if analysis.security_level == SecurityLevel.SAFE and len(filtered_data) < 1000:
                self._cache_result(query_id, result)

            # Record performance metrics
            self._record_performance_metrics(tenant_context.tenant_id, result)

            return result

        except Exception as e:
            logger.error(f"Error processing NLP query for tenant {tenant_context.tenant_id}: {e}")
            raise

    async def _analyze_query(self, natural_query: str, schema_info: TenantSchemaInfo,
                           tenant_context: TenantRoutingContext) -> QueryAnalysis:
        """Analyze the natural language query."""

        # Basic query type detection
        query_lower = natural_query.lower()

        if any(word in query_lower for word in ['count', 'sum', 'avg', 'average', 'total']):
            query_type = QueryType.AGGREGATE
        elif any(word in query_lower for word in ['join', 'relate', 'connect', 'combine']):
            query_type = QueryType.JOIN
        elif any(word in query_lower for word in ['where', 'filter', 'only', 'specific']):
            query_type = QueryType.FILTER
        elif any(word in query_lower for word in ['group', 'category', 'by']):
            query_type = QueryType.GROUPBY
        elif any(word in query_lower for word in ['order', 'sort', 'arrange']):
            query_type = QueryType.ORDERBY
        else:
            query_type = QueryType.SELECT

        # Detect tables involved
        tables_involved = []
        for table_name in schema_info.tables.keys():
            if table_name.lower() in query_lower or any(
                word in query_lower for word in table_name.lower().split('_')
            ):
                tables_involved.append(table_name)

        # Detect columns involved
        columns_involved = []
        for table_name, table_info in schema_info.tables.items():
            if table_name in tables_involved:
                for column_name in table_info['columns'].keys():
                    if column_name.lower() in query_lower:
                        columns_involved.append(f"{table_name}.{column_name}")

        # Security analysis
        security_level = self.security_analyzer.analyze_query_security(
            natural_query, tables_involved, tenant_context.access_level
        )

        # Complexity estimation
        complexity = 1
        if query_type == QueryType.JOIN:
            complexity += 2
        if query_type == QueryType.AGGREGATE:
            complexity += 1
        if len(tables_involved) > 1:
            complexity += len(tables_involved) - 1

        # Confidence score (simplified)
        confidence = 0.8
        if not tables_involved:
            confidence = 0.3
        elif len(tables_involved) == 1 and columns_involved:
            confidence = 0.9

        return QueryAnalysis(
            original_query=natural_query,
            query_type=query_type,
            tables_involved=tables_involved,
            columns_involved=columns_involved,
            security_level=security_level,
            estimated_complexity=complexity,
            requires_joins=len(tables_involved) > 1,
            has_aggregations=query_type == QueryType.AGGREGATE,
            filter_conditions=[],
            confidence_score=confidence
        )

    async def _generate_tenant_sql(self, natural_query: str, schema_info: TenantSchemaInfo,
                                 analysis: QueryAnalysis, tenant_context: TenantRoutingContext) -> str:
        """Generate SQL query with tenant-specific schema awareness."""

        # Use the original NLP2SQL engine but with tenant schema context
        tenant_schema_context = {
            'tables': schema_info.tables,
            'relationships': schema_info.relationships,
            'database_type': schema_info.database_type.value
        }

        # Enhanced prompt with tenant schema information
        enhanced_prompt = self._build_enhanced_prompt(
            natural_query, schema_info, analysis, tenant_context
        )

        # Generate SQL using the original engine with enhanced context
        try:
            if hasattr(self.original_engine, 'generate_sql_with_context'):
                generated_sql = await self.original_engine.generate_sql_with_context(
                    enhanced_prompt, tenant_schema_context
                )
            else:
                # Fallback to basic SQL generation
                generated_sql = self._generate_basic_sql(natural_query, analysis, schema_info)

            # Add tenant-specific safety clauses
            safe_sql = self._add_safety_clauses(generated_sql, tenant_context, schema_info)

            return safe_sql

        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            # Fallback to basic SQL generation
            return self._generate_basic_sql(natural_query, analysis, schema_info)

    def _build_enhanced_prompt(self, natural_query: str, schema_info: TenantSchemaInfo,
                             analysis: QueryAnalysis, tenant_context: TenantRoutingContext) -> str:
        """Build enhanced prompt with tenant schema context."""

        schema_description = []
        for table_name, table_info in schema_info.tables.items():
            columns = [f"{col} ({info['type']})" for col, info in table_info['columns'].items()]
            schema_description.append(f"Table {table_name}: {', '.join(columns)}")

        relationships_description = []
        for rel in schema_info.relationships:
            relationships_description.append(
                f"{rel['from_table']}.{rel['from_column']} -> {rel['to_table']}.{rel['to_column']}"
            )

        prompt = f"""
        Convert the following natural language query to SQL.

        Natural Language Query: {natural_query}

        Database Schema:
        {chr(10).join(schema_description)}

        Relationships:
        {chr(10).join(relationships_description)}

        Database Type: {schema_info.database_type.value}
        User Access Level: {tenant_context.access_level}

        Guidelines:
        - Only use tables and columns that exist in the schema
        - Respect the relationships between tables
        - Generate efficient queries appropriate for {schema_info.database_type.value}
        - Limit results to reasonable amounts for access level {tenant_context.access_level}
        - Use appropriate JOINs when accessing multiple tables

        Generate only the SQL query without explanations:
        """

        return prompt

    def _generate_basic_sql(self, natural_query: str, analysis: QueryAnalysis,
                          schema_info: TenantSchemaInfo) -> str:
        """Generate basic SQL as fallback."""

        if not analysis.tables_involved:
            raise Exception("No tables identified in query")

        # Simple SQL generation logic
        if analysis.query_type == QueryType.SELECT:
            tables = analysis.tables_involved[0]
            if analysis.columns_involved:
                columns = ", ".join([col.split('.')[-1] for col in analysis.columns_involved])
            else:
                columns = "*"

            sql = f"SELECT {columns} FROM {tables}"

            # Add LIMIT for safety
            if analysis.security_level != SecurityLevel.ADMIN_ONLY:
                sql += " LIMIT 100"

            return sql

        elif analysis.query_type == QueryType.AGGREGATE:
            table = analysis.tables_involved[0]
            return f"SELECT COUNT(*) as total_count FROM {table} LIMIT 1"

        else:
            # Default to safe SELECT
            table = analysis.tables_involved[0]
            return f"SELECT * FROM {table} LIMIT 10"

    def _add_safety_clauses(self, sql: str, tenant_context: TenantRoutingContext,
                          schema_info: TenantSchemaInfo) -> str:
        """Add safety clauses to SQL query."""

        # Add LIMIT if not present and user is not admin
        if tenant_context.access_level not in ['ADMIN', 'SUPER_ADMIN']:
            if 'LIMIT' not in sql.upper():
                if tenant_context.access_level == 'VIEWER':
                    sql += " LIMIT 50"
                else:
                    sql += " LIMIT 500"

        return sql

    async def _execute_tenant_query(self, sql: str, tenant_context: TenantRoutingContext,
                                  analysis: QueryAnalysis) -> Dict[str, Any]:
        """Execute SQL query with tenant isolation."""

        try:
            with self.connection_manager.get_connection_context(tenant_context.tenant_id) as connection:

                # Execute query based on database type
                tenant_info = self.connection_manager.get_tenant_info(tenant_context.tenant_id)

                if tenant_info.database_type in [DatabaseType.MYSQL, DatabaseType.POSTGRESQL, DatabaseType.SQLITE]:
                    result = connection.execute(text(sql))

                    # Convert to list of dictionaries
                    columns = result.keys()
                    data = [dict(zip(columns, row)) for row in result.fetchall()]

                elif tenant_info.database_type == DatabaseType.MONGODB:
                    # Convert SQL-like query to MongoDB query (simplified)
                    # This would need a more sophisticated SQL-to-MongoDB translator
                    collection_name = analysis.tables_involved[0] if analysis.tables_involved else "default"
                    data = list(connection[collection_name].find().limit(100))

                else:
                    raise Exception(f"Unsupported database type: {tenant_info.database_type}")

                return {
                    'data': data,
                    'row_count': len(data),
                    'execution_successful': True
                }

        except Exception as e:
            logger.error(f"Error executing tenant query: {e}")
            raise

    def _generate_query_id(self, query: str, tenant_id: str) -> str:
        """Generate unique query ID for caching."""
        query_hash = hashlib.md5(f"{query}:{tenant_id}".encode()).hexdigest()
        return f"query_{query_hash}"

    def _get_cached_result(self, query_id: str, tenant_context: TenantRoutingContext) -> Optional[QueryResult]:
        """Get cached query result."""
        with self.cache_lock:
            if query_id in self.query_cache:
                cached_result = self.query_cache[query_id]

                # Check if cache is still valid
                cache_age = (datetime.utcnow() - datetime.fromisoformat(
                    cached_result.metadata.get('cached_at', '2000-01-01T00:00:00')
                )).seconds

                if cache_age < self.cache_ttl:
                    cached_result.cached = True
                    return cached_result
                else:
                    # Remove expired cache
                    del self.query_cache[query_id]

        return None

    def _cache_result(self, query_id: str, result: QueryResult):
        """Cache query result."""
        with self.cache_lock:
            # Add cache timestamp
            result.metadata['cached_at'] = datetime.utcnow().isoformat()

            # Store in cache
            self.query_cache[query_id] = result

            # Limit cache size
            if len(self.query_cache) > 1000:
                # Remove oldest entries
                oldest_keys = sorted(
                    self.query_cache.keys(),
                    key=lambda k: self.query_cache[k].metadata.get('cached_at', '2000-01-01T00:00:00')
                )[:100]

                for key in oldest_keys:
                    del self.query_cache[key]

    def _record_performance_metrics(self, tenant_id: str, result: QueryResult):
        """Record performance metrics for monitoring."""
        try:
            if tenant_id not in self.performance_metrics:
                self.performance_metrics[tenant_id] = {
                    'total_queries': 0,
                    'successful_queries': 0,
                    'avg_execution_time_ms': 0,
                    'cache_hit_rate': 0,
                    'last_query_time': None
                }

            metrics = self.performance_metrics[tenant_id]
            metrics['total_queries'] += 1
            metrics['successful_queries'] += 1

            # Update average execution time
            if metrics['avg_execution_time_ms'] == 0:
                metrics['avg_execution_time_ms'] = result.execution_time_ms
            else:
                metrics['avg_execution_time_ms'] = (
                    metrics['avg_execution_time_ms'] * 0.9 + result.execution_time_ms * 0.1
                )

            metrics['last_query_time'] = datetime.utcnow().isoformat()

        except Exception as e:
            logger.error(f"Error recording performance metrics: {e}")

    def get_tenant_metrics(self, tenant_id: str = None) -> Dict[str, Any]:
        """Get performance metrics for tenant(s)."""
        if tenant_id:
            return self.performance_metrics.get(tenant_id, {})
        return self.performance_metrics

    def clear_cache(self, tenant_id: str = None):
        """Clear query cache for tenant or all tenants."""
        with self.cache_lock:
            if tenant_id:
                # Clear cache for specific tenant
                keys_to_remove = [
                    key for key, result in self.query_cache.items()
                    if result.tenant_id == tenant_id
                ]
                for key in keys_to_remove:
                    del self.query_cache[key]
            else:
                # Clear all cache
                self.query_cache.clear()

    def refresh_tenant_schema(self, tenant_id: str) -> bool:
        """Refresh schema cache for tenant."""
        try:
            self.schema_manager.get_tenant_schema(tenant_id, force_refresh=True)
            self.clear_cache(tenant_id)  # Clear query cache as schema changed
            return True
        except Exception as e:
            logger.error(f"Error refreshing schema for tenant {tenant_id}: {e}")
            return False