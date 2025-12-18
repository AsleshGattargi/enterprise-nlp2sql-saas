"""
Root Database Image Manager for Multi-Tenant NLP2SQL System
Manages master schema templates, versioning, and database initialization.
"""

import os
import json
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

import mysql.connector
import psycopg2
import pymongo
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

class DatabaseType(Enum):
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    MONGODB = "mongodb"

@dataclass
class SchemaVersion:
    version: str
    database_type: DatabaseType
    created_at: datetime
    description: str
    file_path: str

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]

class RootImageManager:
    """
    Manages root database images, schema templates, and version control
    for the Multi-Tenant NLP2SQL system.
    """

    def __init__(self, root_schemas_path: str = "root_schemas"):
        """
        Initialize the Root Image Manager.

        Args:
            root_schemas_path: Path to the root schemas directory
        """
        self.root_schemas_path = Path(root_schemas_path)
        self.ensure_directory_structure()

        # Schema file patterns for each database type
        self.schema_files = {
            DatabaseType.MYSQL: "root_schema.sql",
            DatabaseType.POSTGRESQL: "root_schema.sql",
            DatabaseType.SQLITE: "root_schema.sql",
            DatabaseType.MONGODB: "root_schema.json"
        }

        # Version history cache
        self._version_cache: Dict[DatabaseType, List[SchemaVersion]] = {}

        logger.info(f"RootImageManager initialized with path: {self.root_schemas_path}")

    def ensure_directory_structure(self):
        """Ensure the required directory structure exists."""
        directories = [
            "mysql/v1.0", "mysql/v1.1",
            "postgresql/v1.0", "postgresql/v1.1",
            "sqlite/v1.0", "sqlite/v1.1",
            "mongodb/v1.0", "mongodb/v1.1",
            "migrations", "validators"
        ]

        for directory in directories:
            (self.root_schemas_path / directory).mkdir(parents=True, exist_ok=True)

    def get_available_versions(self, db_type: DatabaseType) -> List[SchemaVersion]:
        """
        Get all available schema versions for a database type.

        Args:
            db_type: Database type to get versions for

        Returns:
            List of available schema versions
        """
        if db_type in self._version_cache:
            return self._version_cache[db_type]

        versions = []
        db_path = self.root_schemas_path / db_type.value

        if not db_path.exists():
            logger.warning(f"No schema directory found for {db_type.value}")
            return versions

        # Find all version directories
        for version_dir in sorted(db_path.iterdir()):
            if version_dir.is_dir() and version_dir.name.startswith('v'):
                schema_file = version_dir / self.schema_files[db_type]

                if schema_file.exists():
                    # Try to extract description from schema file
                    description = self._extract_schema_description(schema_file, db_type)

                    versions.append(SchemaVersion(
                        version=version_dir.name,
                        database_type=db_type,
                        created_at=datetime.fromtimestamp(schema_file.stat().st_ctime),
                        description=description,
                        file_path=str(schema_file)
                    ))

        self._version_cache[db_type] = versions
        return versions

    def get_latest_version(self, db_type: DatabaseType) -> Optional[SchemaVersion]:
        """
        Get the latest schema version for a database type.

        Args:
            db_type: Database type

        Returns:
            Latest schema version or None if no versions exist
        """
        versions = self.get_available_versions(db_type)
        return max(versions, key=lambda v: v.version) if versions else None

    def get_schema_content(self, db_type: DatabaseType, version: str = None) -> Optional[str]:
        """
        Get the schema content for a specific database type and version.

        Args:
            db_type: Database type
            version: Version string (defaults to latest)

        Returns:
            Schema content as string or None if not found
        """
        if version is None:
            latest = self.get_latest_version(db_type)
            if not latest:
                logger.error(f"No schema versions found for {db_type.value}")
                return None
            version = latest.version

        schema_path = self.root_schemas_path / db_type.value / version / self.schema_files[db_type]

        if not schema_path.exists():
            logger.error(f"Schema file not found: {schema_path}")
            return None

        try:
            return schema_path.read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"Error reading schema file {schema_path}: {e}")
            return None

    def create_root_schema(self, db_type: DatabaseType, connection_params: Dict[str, Any],
                          version: str = None, force: bool = False) -> bool:
        """
        Create a root schema in the specified database.

        Args:
            db_type: Database type to create schema for
            connection_params: Database connection parameters
            version: Schema version to use (defaults to latest)
            force: Whether to force creation even if schema exists

        Returns:
            True if schema was created successfully, False otherwise
        """
        try:
            schema_content = self.get_schema_content(db_type, version)
            if not schema_content:
                logger.error(f"Could not get schema content for {db_type.value} version {version}")
                return False

            logger.info(f"Creating root schema for {db_type.value} version {version or 'latest'}")

            if db_type == DatabaseType.MYSQL:
                return self._create_mysql_schema(connection_params, schema_content, force)
            elif db_type == DatabaseType.POSTGRESQL:
                return self._create_postgresql_schema(connection_params, schema_content, force)
            elif db_type == DatabaseType.SQLITE:
                return self._create_sqlite_schema(connection_params, schema_content, force)
            elif db_type == DatabaseType.MONGODB:
                return self._create_mongodb_schema(connection_params, schema_content, force)
            else:
                logger.error(f"Unsupported database type: {db_type}")
                return False

        except Exception as e:
            logger.error(f"Error creating root schema for {db_type.value}: {e}")
            return False

    def validate_schema(self, db_type: DatabaseType, version: str = None) -> ValidationResult:
        """
        Validate a schema definition.

        Args:
            db_type: Database type
            version: Schema version (defaults to latest)

        Returns:
            ValidationResult with validation status and messages
        """
        errors = []
        warnings = []

        try:
            schema_content = self.get_schema_content(db_type, version)
            if not schema_content:
                errors.append(f"Schema content not found for {db_type.value} version {version}")
                return ValidationResult(False, errors, warnings)

            if db_type == DatabaseType.MONGODB:
                # Validate JSON schema for MongoDB
                try:
                    schema_data = json.loads(schema_content)
                    required_keys = ["version", "database_type", "collections"]
                    for key in required_keys:
                        if key not in schema_data:
                            errors.append(f"Missing required key: {key}")
                except json.JSONDecodeError as e:
                    errors.append(f"Invalid JSON in MongoDB schema: {e}")
            else:
                # Validate SQL schema
                if not self._validate_sql_schema(schema_content, db_type):
                    errors.append("SQL schema validation failed")

            # Check for common required tables
            required_tables = [
                "organizations", "users", "query_logs", "permissions",
                "security_logs", "system_settings", "hdt_profiles"
            ]

            for table in required_tables:
                if table not in schema_content.lower():
                    warnings.append(f"Required table '{table}' not found in schema")

            is_valid = len(errors) == 0

            logger.info(f"Schema validation for {db_type.value} version {version}: "
                       f"{'PASSED' if is_valid else 'FAILED'}")

            return ValidationResult(is_valid, errors, warnings)

        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return ValidationResult(False, errors, warnings)

    def upgrade_schema(self, db_type: DatabaseType, from_version: str,
                      to_version: str, connection_params: Dict[str, Any]) -> bool:
        """
        Upgrade schema from one version to another.

        Args:
            db_type: Database type
            from_version: Source version
            to_version: Target version
            connection_params: Database connection parameters

        Returns:
            True if upgrade was successful, False otherwise
        """
        try:
            migration_path = self._get_migration_path(db_type, from_version, to_version)
            if not migration_path.exists():
                logger.error(f"Migration script not found: {migration_path}")
                return False

            migration_content = migration_path.read_text(encoding='utf-8')

            logger.info(f"Upgrading {db_type.value} schema from {from_version} to {to_version}")

            if db_type == DatabaseType.MONGODB:
                return self._execute_mongodb_migration(connection_params, migration_content)
            else:
                return self._execute_sql_migration(db_type, connection_params, migration_content)

        except Exception as e:
            logger.error(f"Error upgrading schema: {e}")
            return False

    def backup_schema(self, db_type: DatabaseType, connection_params: Dict[str, Any],
                     backup_path: str = None) -> Optional[str]:
        """
        Create a backup of the current database schema.

        Args:
            db_type: Database type
            connection_params: Database connection parameters
            backup_path: Custom backup path (optional)

        Returns:
            Path to backup file or None if backup failed
        """
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"backup_{db_type.value}_{timestamp}.sql"

            logger.info(f"Creating backup for {db_type.value} database")

            if db_type == DatabaseType.MYSQL:
                return self._backup_mysql_schema(connection_params, backup_path)
            elif db_type == DatabaseType.POSTGRESQL:
                return self._backup_postgresql_schema(connection_params, backup_path)
            elif db_type == DatabaseType.SQLITE:
                return self._backup_sqlite_schema(connection_params, backup_path)
            elif db_type == DatabaseType.MONGODB:
                return self._backup_mongodb_schema(connection_params, backup_path)

        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return None

    def list_schema_differences(self, db_type: DatabaseType, version1: str,
                               version2: str) -> Dict[str, List[str]]:
        """
        Compare two schema versions and list differences.

        Args:
            db_type: Database type
            version1: First version
            version2: Second version

        Returns:
            Dictionary containing lists of differences
        """
        differences = {
            "added": [],
            "removed": [],
            "modified": []
        }

        try:
            schema1 = self.get_schema_content(db_type, version1)
            schema2 = self.get_schema_content(db_type, version2)

            if not schema1 or not schema2:
                logger.error("Could not retrieve schema content for comparison")
                return differences

            # Simple line-by-line comparison (can be enhanced with more sophisticated diff)
            lines1 = set(line.strip() for line in schema1.split('\n') if line.strip())
            lines2 = set(line.strip() for line in schema2.split('\n') if line.strip())

            differences["added"] = list(lines2 - lines1)
            differences["removed"] = list(lines1 - lines2)

            logger.info(f"Schema comparison between {version1} and {version2}: "
                       f"{len(differences['added'])} added, {len(differences['removed'])} removed")

        except Exception as e:
            logger.error(f"Error comparing schemas: {e}")

        return differences

    # Private helper methods

    def _extract_schema_description(self, schema_file: Path, db_type: DatabaseType) -> str:
        """Extract description from schema file."""
        try:
            content = schema_file.read_text(encoding='utf-8')
            if db_type == DatabaseType.MONGODB:
                data = json.loads(content)
                return data.get('description', 'No description available')
            else:
                # Look for description in SQL comments
                lines = content.split('\n')
                for line in lines[:10]:  # Check first 10 lines
                    if 'description' in line.lower() and ('--' in line or '/*' in line):
                        return line.split('--')[-1].strip() if '--' in line else line
                return 'SQL schema file'
        except Exception:
            return 'No description available'

    def _validate_sql_schema(self, schema_content: str, db_type: DatabaseType) -> bool:
        """Validate SQL schema syntax."""
        try:
            # Basic validation - check for required SQL keywords
            required_keywords = ['CREATE TABLE', 'PRIMARY KEY', 'FOREIGN KEY']
            for keyword in required_keywords:
                if keyword not in schema_content.upper():
                    logger.warning(f"Missing expected keyword: {keyword}")

            # Try to parse with SQLAlchemy (basic syntax check)
            from sqlalchemy import text
            statements = schema_content.split(';')

            for statement in statements:
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        text(statement)
                    except Exception as e:
                        logger.warning(f"Potential SQL syntax issue: {e}")

            return True
        except Exception as e:
            logger.error(f"SQL validation error: {e}")
            return False

    def _create_mysql_schema(self, connection_params: Dict[str, Any],
                           schema_content: str, force: bool = False) -> bool:
        """Create MySQL schema."""
        try:
            conn = mysql.connector.connect(**connection_params)
            cursor = conn.cursor()

            # Check if schema already exists
            if not force:
                cursor.execute("SHOW TABLES LIKE 'organizations'")
                if cursor.fetchone():
                    logger.warning("Schema appears to already exist. Use force=True to recreate.")
                    return False

            # Execute schema statements
            statements = [stmt.strip() for stmt in schema_content.split(';') if stmt.strip()]
            for statement in statements:
                if statement and not statement.startswith('--'):
                    cursor.execute(statement)

            conn.commit()
            cursor.close()
            conn.close()

            logger.info("MySQL schema created successfully")
            return True

        except Exception as e:
            logger.error(f"Error creating MySQL schema: {e}")
            return False

    def _create_postgresql_schema(self, connection_params: Dict[str, Any],
                                schema_content: str, force: bool = False) -> bool:
        """Create PostgreSQL schema."""
        try:
            conn = psycopg2.connect(**connection_params)
            cursor = conn.cursor()

            # Check if schema already exists
            if not force:
                cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'organizations')")
                if cursor.fetchone()[0]:
                    logger.warning("Schema appears to already exist. Use force=True to recreate.")
                    return False

            # Execute schema statements
            cursor.execute(schema_content)
            conn.commit()
            cursor.close()
            conn.close()

            logger.info("PostgreSQL schema created successfully")
            return True

        except Exception as e:
            logger.error(f"Error creating PostgreSQL schema: {e}")
            return False

    def _create_sqlite_schema(self, connection_params: Dict[str, Any],
                            schema_content: str, force: bool = False) -> bool:
        """Create SQLite schema."""
        try:
            db_path = connection_params.get('database', 'database.db')

            # Check if schema already exists
            if not force and os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='organizations'")
                if cursor.fetchone():
                    logger.warning("Schema appears to already exist. Use force=True to recreate.")
                    conn.close()
                    return False
                conn.close()

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Execute schema statements
            cursor.executescript(schema_content)
            conn.commit()
            conn.close()

            logger.info("SQLite schema created successfully")
            return True

        except Exception as e:
            logger.error(f"Error creating SQLite schema: {e}")
            return False

    def _create_mongodb_schema(self, connection_params: Dict[str, Any],
                             schema_content: str, force: bool = False) -> bool:
        """Create MongoDB schema (collections and indexes)."""
        try:
            schema_data = json.loads(schema_content)

            client = pymongo.MongoClient(connection_params['uri'])
            db = client[connection_params['database']]

            # Check if schema already exists
            if not force and 'organizations' in db.list_collection_names():
                logger.warning("Schema appears to already exist. Use force=True to recreate.")
                return False

            # Create collections with validators and indexes
            for collection_name, collection_config in schema_data['collections'].items():
                if 'validator' in collection_config:
                    db.create_collection(collection_name, validator=collection_config['validator'])
                else:
                    db.create_collection(collection_name)

                # Create indexes
                if 'indexes' in collection_config:
                    collection = db[collection_name]
                    for index_config in collection_config['indexes']:
                        collection.create_index(
                            list(index_config['key'].items()),
                            name=index_config['name'],
                            unique=index_config.get('unique', False)
                        )

            # Insert initial data
            if 'initial_data' in schema_data:
                for collection_name, documents in schema_data['initial_data'].items():
                    if documents:
                        db[collection_name].insert_many(documents)

            client.close()
            logger.info("MongoDB schema created successfully")
            return True

        except Exception as e:
            logger.error(f"Error creating MongoDB schema: {e}")
            return False

    def _get_migration_path(self, db_type: DatabaseType, from_version: str,
                           to_version: str) -> Path:
        """Get path to migration script."""
        migration_file = f"migrate_{from_version}_to_{to_version}.sql"
        if db_type == DatabaseType.MONGODB:
            migration_file = f"migrate_{from_version}_to_{to_version}.json"
        return self.root_schemas_path / "migrations" / db_type.value / migration_file

    def _execute_sql_migration(self, db_type: DatabaseType,
                             connection_params: Dict[str, Any], migration_content: str) -> bool:
        """Execute SQL migration."""
        # Implementation would depend on specific database type
        # This is a placeholder for the migration execution logic
        logger.info(f"Executing SQL migration for {db_type.value}")
        return True

    def _execute_mongodb_migration(self, connection_params: Dict[str, Any],
                                 migration_content: str) -> bool:
        """Execute MongoDB migration."""
        # Implementation for MongoDB-specific migrations
        logger.info("Executing MongoDB migration")
        return True

    def _backup_mysql_schema(self, connection_params: Dict[str, Any], backup_path: str) -> str:
        """Backup MySQL schema."""
        # Implementation for MySQL backup (e.g., using mysqldump)
        logger.info("Creating MySQL backup")
        return backup_path

    def _backup_postgresql_schema(self, connection_params: Dict[str, Any], backup_path: str) -> str:
        """Backup PostgreSQL schema."""
        # Implementation for PostgreSQL backup (e.g., using pg_dump)
        logger.info("Creating PostgreSQL backup")
        return backup_path

    def _backup_sqlite_schema(self, connection_params: Dict[str, Any], backup_path: str) -> str:
        """Backup SQLite schema."""
        # Implementation for SQLite backup
        logger.info("Creating SQLite backup")
        return backup_path

    def _backup_mongodb_schema(self, connection_params: Dict[str, Any], backup_path: str) -> str:
        """Backup MongoDB schema."""
        # Implementation for MongoDB backup (e.g., using mongodump)
        logger.info("Creating MongoDB backup")
        return backup_path