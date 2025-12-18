"""
Schema Validation System for Multi-Tenant NLP2SQL
Comprehensive validation of database schemas for integrity, performance, and compliance.
"""

import json
import sqlite3
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass
from enum import Enum

import mysql.connector
import psycopg2
import pymongo
import sqlparse
from sqlparse import sql, tokens

logger = logging.getLogger(__name__)

class ValidationSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

@dataclass
class ValidationIssue:
    severity: ValidationSeverity
    category: str
    message: str
    table: Optional[str] = None
    column: Optional[str] = None
    line_number: Optional[int] = None

@dataclass
class SchemaValidationResult:
    is_valid: bool
    score: float  # 0-100 validation score
    issues: List[ValidationIssue]
    performance_warnings: List[str]
    security_warnings: List[str]
    compliance_issues: List[str]

class SchemaValidator:
    """
    Comprehensive schema validator for Multi-Tenant NLP2SQL system.
    Validates schema integrity, performance, security, and compliance.
    """

    def __init__(self, validation_rules_path: str = "root_schemas/schema_versions.json"):
        """Initialize schema validator with validation rules."""
        self.validation_rules_path = Path(validation_rules_path)
        self.validation_rules = self._load_validation_rules()

        # Required tables for multi-tenant system
        self.required_tables = set(self.validation_rules.get('validation_rules', {})
                                 .get('required_tables', []))

        # Performance-critical indexes
        self.required_indexes = self.validation_rules.get('validation_rules', {}) \
                                .get('required_indexes', {})

        # Required constraints
        self.required_constraints = self.validation_rules.get('validation_rules', {}) \
                                  .get('required_constraints', {})

        logger.info("SchemaValidator initialized")

    def _load_validation_rules(self) -> Dict:
        """Load validation rules from configuration file."""
        try:
            if self.validation_rules_path.exists():
                with open(self.validation_rules_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning(f"Validation rules file not found: {self.validation_rules_path}")
                return {}
        except Exception as e:
            logger.error(f"Error loading validation rules: {e}")
            return {}

    def validate_schema(self, schema_content: str, db_type: str,
                       connection_params: Dict = None) -> SchemaValidationResult:
        """
        Perform comprehensive schema validation.

        Args:
            schema_content: Schema definition content
            db_type: Database type (mysql, postgresql, sqlite, mongodb)
            connection_params: Optional database connection for live validation

        Returns:
            SchemaValidationResult with validation details
        """
        issues = []
        performance_warnings = []
        security_warnings = []
        compliance_issues = []

        logger.info(f"Starting schema validation for {db_type}")

        try:
            if db_type.lower() == 'mongodb':
                issues.extend(self._validate_mongodb_schema(schema_content))
            else:
                issues.extend(self._validate_sql_schema(schema_content, db_type))

            # Structure validation
            issues.extend(self._validate_required_tables(schema_content, db_type))
            issues.extend(self._validate_required_indexes(schema_content, db_type))
            issues.extend(self._validate_constraints(schema_content, db_type))

            # Security validation
            security_warnings.extend(self._validate_security(schema_content, db_type))

            # Performance validation
            performance_warnings.extend(self._validate_performance(schema_content, db_type))

            # Compliance validation
            compliance_issues.extend(self._validate_compliance(schema_content, db_type))

            # Live database validation if connection provided
            if connection_params:
                live_issues = self._validate_live_database(connection_params, db_type)
                issues.extend(live_issues)

            # Calculate validation score
            score = self._calculate_validation_score(issues, performance_warnings,
                                                   security_warnings, compliance_issues)

            is_valid = all(issue.severity != ValidationSeverity.ERROR for issue in issues)

            logger.info(f"Schema validation completed. Score: {score}/100, Valid: {is_valid}")

            return SchemaValidationResult(
                is_valid=is_valid,
                score=score,
                issues=issues,
                performance_warnings=performance_warnings,
                security_warnings=security_warnings,
                compliance_issues=compliance_issues
            )

        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            return SchemaValidationResult(
                is_valid=False,
                score=0.0,
                issues=[ValidationIssue(
                    ValidationSeverity.ERROR,
                    "validation_error",
                    f"Validation process failed: {str(e)}"
                )],
                performance_warnings=[],
                security_warnings=[],
                compliance_issues=[]
            )

    def _validate_sql_schema(self, schema_content: str, db_type: str) -> List[ValidationIssue]:
        """Validate SQL schema syntax and structure."""
        issues = []

        try:
            # Parse SQL statements
            statements = sqlparse.split(schema_content)

            for i, statement in enumerate(statements):
                if not statement.strip() or statement.strip().startswith('--'):
                    continue

                # Parse individual statement
                parsed = sqlparse.parse(statement)[0]

                # Validate CREATE TABLE statements
                if self._is_create_table_statement(parsed):
                    table_issues = self._validate_create_table(parsed, db_type, i + 1)
                    issues.extend(table_issues)

                # Validate CREATE INDEX statements
                elif self._is_create_index_statement(parsed):
                    index_issues = self._validate_create_index(parsed, db_type, i + 1)
                    issues.extend(index_issues)

                # Check for syntax errors
                if self._has_syntax_errors(parsed):
                    issues.append(ValidationIssue(
                        ValidationSeverity.ERROR,
                        "syntax_error",
                        f"SQL syntax error in statement {i + 1}",
                        line_number=i + 1
                    ))

        except Exception as e:
            issues.append(ValidationIssue(
                ValidationSeverity.ERROR,
                "parsing_error",
                f"Failed to parse SQL schema: {str(e)}"
            ))

        return issues

    def _validate_mongodb_schema(self, schema_content: str) -> List[ValidationIssue]:
        """Validate MongoDB schema definition."""
        issues = []

        try:
            schema_data = json.loads(schema_content)

            # Validate required top-level keys
            required_keys = ['version', 'database_type', 'collections']
            for key in required_keys:
                if key not in schema_data:
                    issues.append(ValidationIssue(
                        ValidationSeverity.ERROR,
                        "missing_key",
                        f"Missing required key: {key}"
                    ))

            # Validate collections
            collections = schema_data.get('collections', {})
            for collection_name, collection_config in collections.items():
                collection_issues = self._validate_mongodb_collection(
                    collection_name, collection_config
                )
                issues.extend(collection_issues)

        except json.JSONDecodeError as e:
            issues.append(ValidationIssue(
                ValidationSeverity.ERROR,
                "json_error",
                f"Invalid JSON in MongoDB schema: {str(e)}"
            ))

        return issues

    def _validate_required_tables(self, schema_content: str, db_type: str) -> List[ValidationIssue]:
        """Validate that all required tables are present."""
        issues = []
        content_lower = schema_content.lower()

        for table_name in self.required_tables:
            if db_type.lower() == 'mongodb':
                # Check for collection definition in JSON
                if f'"{table_name}"' not in schema_content:
                    issues.append(ValidationIssue(
                        ValidationSeverity.ERROR,
                        "missing_table",
                        f"Required collection '{table_name}' not found in schema"
                    ))
            else:
                # Check for CREATE TABLE statement
                if f"create table {table_name}" not in content_lower and \
                   f"create table if not exists {table_name}" not in content_lower:
                    issues.append(ValidationIssue(
                        ValidationSeverity.ERROR,
                        "missing_table",
                        f"Required table '{table_name}' not found in schema"
                    ))

        return issues

    def _validate_required_indexes(self, schema_content: str, db_type: str) -> List[ValidationIssue]:
        """Validate that required indexes are present."""
        issues = []
        content_lower = schema_content.lower()

        for table_name, required_idx_columns in self.required_indexes.items():
            for column in required_idx_columns:
                if db_type.lower() == 'mongodb':
                    # Check MongoDB index definitions
                    if f'"key": {{"{column}": 1}}' not in schema_content and \
                       f'"key": {{"{column}": -1}}' not in schema_content:
                        issues.append(ValidationIssue(
                            ValidationSeverity.WARNING,
                            "missing_index",
                            f"Recommended index on {table_name}.{column} not found",
                            table=table_name,
                            column=column
                        ))
                else:
                    # Check SQL index definitions
                    index_patterns = [
                        f"index idx_{column}",
                        f"index {column}",
                        f"key idx_{column}",
                        f"key {column}"
                    ]

                    if not any(pattern in content_lower for pattern in index_patterns):
                        issues.append(ValidationIssue(
                            ValidationSeverity.WARNING,
                            "missing_index",
                            f"Recommended index on {table_name}.{column} not found",
                            table=table_name,
                            column=column
                        ))

        return issues

    def _validate_constraints(self, schema_content: str, db_type: str) -> List[ValidationIssue]:
        """Validate foreign key and unique constraints."""
        issues = []
        content_lower = schema_content.lower()

        # Check foreign keys
        foreign_keys = self.required_constraints.get('foreign_keys', [])
        for fk_constraint in foreign_keys:
            # Parse constraint like "users.org_id -> organizations.org_id"
            if ' -> ' in fk_constraint:
                child_table_column, parent_table_column = fk_constraint.split(' -> ')
                child_table = child_table_column.split('.')[0]

                if db_type.lower() != 'mongodb':  # MongoDB doesn't have foreign keys
                    if f"foreign key" not in content_lower or \
                       f"references {parent_table_column.split('.')[0]}" not in content_lower:
                        issues.append(ValidationIssue(
                            ValidationSeverity.WARNING,
                            "missing_constraint",
                            f"Foreign key constraint {fk_constraint} not found",
                            table=child_table
                        ))

        # Check unique constraints
        unique_constraints = self.required_constraints.get('unique_constraints', [])
        for constraint in unique_constraints:
            if 'unique' not in content_lower or constraint.lower() not in content_lower:
                issues.append(ValidationIssue(
                    ValidationSeverity.WARNING,
                    "missing_constraint",
                    f"Unique constraint on '{constraint}' not found"
                ))

        return issues

    def _validate_security(self, schema_content: str, db_type: str) -> List[str]:
        """Validate security aspects of the schema."""
        warnings = []
        content_lower = schema_content.lower()

        # Check for password storage
        if 'password' in content_lower and 'hash' not in content_lower:
            warnings.append("Password field found without 'hash' - ensure passwords are hashed")

        # Check for audit trails
        if 'security_logs' not in content_lower:
            warnings.append("No security audit logging table found")

        # Check for user activity tracking
        if 'last_login' not in content_lower:
            warnings.append("No user activity tracking (last_login) found")

        # Check for API token security
        if 'api_tokens' in content_lower and 'expires_at' not in content_lower:
            warnings.append("API tokens without expiration found - security risk")

        return warnings

    def _validate_performance(self, schema_content: str, db_type: str) -> List[str]:
        """Validate performance aspects of the schema."""
        warnings = []
        content_lower = schema_content.lower()

        # Check for timestamp indexes
        if 'timestamp' in content_lower:
            if 'index' not in content_lower or 'idx_timestamp' not in content_lower:
                warnings.append("Timestamp columns found without indexes - may impact query performance")

        # Check for large text fields without limits
        text_fields = re.findall(r'text\s+(?:not\s+)?null', content_lower)
        if text_fields and db_type.lower() in ['mysql', 'postgresql']:
            warnings.append("Unlimited TEXT fields found - consider adding length limits for better performance")

        # Check for missing primary keys
        tables_with_create = re.findall(r'create\s+table\s+(?:if\s+not\s+exists\s+)?(\w+)', content_lower)
        for table in tables_with_create:
            if f"primary key" not in content_lower:
                warnings.append(f"Table '{table}' may be missing a primary key")

        return warnings

    def _validate_compliance(self, schema_content: str, db_type: str) -> List[str]:
        """Validate compliance aspects of the schema."""
        issues = []
        content_lower = schema_content.lower()

        # Check for GDPR compliance fields
        gdpr_fields = ['created_at', 'updated_at', 'is_active']
        for field in gdpr_fields:
            if field not in content_lower:
                issues.append(f"Missing {field} field - required for GDPR compliance")

        # Check for data retention fields
        if 'expires_at' not in content_lower and 'retention' not in content_lower:
            issues.append("No data retention mechanism found - may violate data protection regulations")

        # Check for consent tracking
        if 'users' in content_lower and 'consent' not in content_lower:
            issues.append("User table without consent tracking - GDPR compliance issue")

        return issues

    def _validate_live_database(self, connection_params: Dict, db_type: str) -> List[ValidationIssue]:
        """Validate live database structure."""
        issues = []

        try:
            if db_type.lower() == 'mysql':
                issues.extend(self._validate_live_mysql(connection_params))
            elif db_type.lower() == 'postgresql':
                issues.extend(self._validate_live_postgresql(connection_params))
            elif db_type.lower() == 'sqlite':
                issues.extend(self._validate_live_sqlite(connection_params))
            elif db_type.lower() == 'mongodb':
                issues.extend(self._validate_live_mongodb(connection_params))

        except Exception as e:
            issues.append(ValidationIssue(
                ValidationSeverity.ERROR,
                "connection_error",
                f"Failed to connect to live database: {str(e)}"
            ))

        return issues

    def _calculate_validation_score(self, issues: List[ValidationIssue],
                                  performance_warnings: List[str],
                                  security_warnings: List[str],
                                  compliance_issues: List[str]) -> float:
        """Calculate overall validation score (0-100)."""
        score = 100.0

        # Deduct points for issues
        for issue in issues:
            if issue.severity == ValidationSeverity.ERROR:
                score -= 10.0
            elif issue.severity == ValidationSeverity.WARNING:
                score -= 5.0
            else:  # INFO
                score -= 1.0

        # Deduct points for warnings and compliance issues
        score -= len(performance_warnings) * 2.0
        score -= len(security_warnings) * 3.0
        score -= len(compliance_issues) * 4.0

        return max(0.0, min(100.0, score))

    # Helper methods for SQL parsing and validation

    def _is_create_table_statement(self, parsed) -> bool:
        """Check if parsed statement is CREATE TABLE."""
        return str(parsed).strip().upper().startswith('CREATE TABLE')

    def _is_create_index_statement(self, parsed) -> bool:
        """Check if parsed statement is CREATE INDEX."""
        return str(parsed).strip().upper().startswith('CREATE INDEX')

    def _has_syntax_errors(self, parsed) -> bool:
        """Basic syntax error detection."""
        # This is a simplified check - can be enhanced
        statement_str = str(parsed).strip()
        if not statement_str:
            return False

        # Check for incomplete statements
        if statement_str.upper().startswith('CREATE') and not statement_str.endswith(';'):
            if 'CREATE TABLE' in statement_str.upper() and ')' not in statement_str:
                return True

        return False

    def _validate_create_table(self, parsed, db_type: str, line_number: int) -> List[ValidationIssue]:
        """Validate CREATE TABLE statement."""
        issues = []

        # Extract table name
        statement_str = str(parsed)

        # Basic validation for required elements
        if 'PRIMARY KEY' not in statement_str.upper():
            issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                "missing_primary_key",
                f"CREATE TABLE statement may be missing PRIMARY KEY",
                line_number=line_number
            ))

        return issues

    def _validate_create_index(self, parsed, db_type: str, line_number: int) -> List[ValidationIssue]:
        """Validate CREATE INDEX statement."""
        issues = []
        # Add specific index validation logic here
        return issues

    def _validate_mongodb_collection(self, collection_name: str,
                                   collection_config: Dict) -> List[ValidationIssue]:
        """Validate MongoDB collection configuration."""
        issues = []

        # Check for validator
        if 'validator' not in collection_config:
            issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                "missing_validator",
                f"Collection '{collection_name}' has no validator defined",
                table=collection_name
            ))

        # Check for indexes
        if 'indexes' not in collection_config:
            issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                "missing_indexes",
                f"Collection '{collection_name}' has no indexes defined",
                table=collection_name
            ))

        return issues

    def _validate_live_mysql(self, connection_params: Dict) -> List[ValidationIssue]:
        """Validate live MySQL database."""
        issues = []
        # Implementation for live MySQL validation
        return issues

    def _validate_live_postgresql(self, connection_params: Dict) -> List[ValidationIssue]:
        """Validate live PostgreSQL database."""
        issues = []
        # Implementation for live PostgreSQL validation
        return issues

    def _validate_live_sqlite(self, connection_params: Dict) -> List[ValidationIssue]:
        """Validate live SQLite database."""
        issues = []
        # Implementation for live SQLite validation
        return issues

    def _validate_live_mongodb(self, connection_params: Dict) -> List[ValidationIssue]:
        """Validate live MongoDB database."""
        issues = []
        # Implementation for live MongoDB validation
        return issues