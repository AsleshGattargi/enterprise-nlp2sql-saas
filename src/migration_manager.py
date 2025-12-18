"""
Migration Manager for Multi-Tenant NLP2SQL System
Handles database schema migrations with rollback support and validation.
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

import mysql.connector
import psycopg2
import pymongo

from .root_image_manager import DatabaseType
from .schema_version_manager import SchemaVersionManager

logger = logging.getLogger(__name__)

class MigrationStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

@dataclass
class MigrationRecord:
    migration_id: str
    from_version: str
    to_version: str
    database_type: DatabaseType
    status: MigrationStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    rollback_available: bool = False

class MigrationManager:
    """
    Manages database schema migrations for the Multi-Tenant NLP2SQL system.
    Provides migration execution, rollback, and validation capabilities.
    """

    def __init__(self, migrations_path: str = "root_schemas/migrations",
                 version_manager: SchemaVersionManager = None):
        """
        Initialize the Migration Manager.

        Args:
            migrations_path: Path to migration scripts directory
            version_manager: Schema version manager instance
        """
        self.migrations_path = Path(migrations_path)
        self.version_manager = version_manager or SchemaVersionManager()

        # Migration records storage (in production, this should be persistent)
        self.migration_records: Dict[str, MigrationRecord] = {}

        logger.info(f"MigrationManager initialized with path: {self.migrations_path}")

    def execute_migration(self, from_version: str, to_version: str,
                         db_type: DatabaseType, connection_params: Dict[str, Any],
                         dry_run: bool = False) -> Tuple[bool, str]:
        """
        Execute a database schema migration.

        Args:
            from_version: Source schema version
            to_version: Target schema version
            db_type: Database type
            connection_params: Database connection parameters
            dry_run: If True, validate migration without executing

        Returns:
            Tuple of (success: bool, message: str)
        """
        migration_id = f"{db_type.value}_{from_version}_to_{to_version}_{datetime.now().isoformat()}"

        try:
            logger.info(f"Starting migration {migration_id}")

            # Validate migration feasibility
            is_feasible, issues = self.version_manager.validate_upgrade_feasibility(
                from_version, to_version, db_type.value
            )

            if not is_feasible:
                error_msg = f"Migration not feasible: {'; '.join(issues)}"
                logger.error(error_msg)
                return False, error_msg

            # Create migration record
            migration_record = MigrationRecord(
                migration_id=migration_id,
                from_version=from_version,
                to_version=to_version,
                database_type=db_type,
                status=MigrationStatus.PENDING,
                started_at=datetime.now()
            )
            self.migration_records[migration_id] = migration_record

            # Pre-migration validation
            pre_validation_passed = self._run_pre_migration_checks(
                db_type, connection_params, from_version
            )

            if not pre_validation_passed:
                migration_record.status = MigrationStatus.FAILED
                migration_record.error_message = "Pre-migration validation failed"
                return False, "Pre-migration validation failed"

            if dry_run:
                logger.info(f"Dry run completed successfully for {migration_id}")
                return True, "Dry run validation passed"

            # Execute migration
            migration_record.status = MigrationStatus.IN_PROGRESS

            if db_type == DatabaseType.MONGODB:
                success, message = self._execute_mongodb_migration(
                    connection_params, from_version, to_version
                )
            else:
                success, message = self._execute_sql_migration(
                    db_type, connection_params, from_version, to_version
                )

            if success:
                migration_record.status = MigrationStatus.COMPLETED
                migration_record.completed_at = datetime.now()
                migration_record.rollback_available = True

                # Post-migration validation
                post_validation_passed = self._run_post_migration_checks(
                    db_type, connection_params, to_version
                )

                if not post_validation_passed:
                    logger.warning("Post-migration validation failed, but migration completed")
                    message += " (Warning: Post-migration validation failed)"

                logger.info(f"Migration {migration_id} completed successfully")
                return True, message
            else:
                migration_record.status = MigrationStatus.FAILED
                migration_record.error_message = message
                logger.error(f"Migration {migration_id} failed: {message}")
                return False, message

        except Exception as e:
            error_msg = f"Migration execution failed: {str(e)}"
            logger.error(error_msg)

            if migration_id in self.migration_records:
                self.migration_records[migration_id].status = MigrationStatus.FAILED
                self.migration_records[migration_id].error_message = error_msg

            return False, error_msg

    def rollback_migration(self, migration_id: str,
                          connection_params: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Rollback a previously executed migration.

        Args:
            migration_id: Migration ID to rollback
            connection_params: Database connection parameters

        Returns:
            Tuple of (success: bool, message: str)
        """
        if migration_id not in self.migration_records:
            return False, f"Migration record not found: {migration_id}"

        migration_record = self.migration_records[migration_id]

        if migration_record.status != MigrationStatus.COMPLETED:
            return False, f"Migration {migration_id} is not in completed state"

        if not migration_record.rollback_available:
            return False, f"Rollback not available for migration {migration_id}"

        try:
            logger.info(f"Starting rollback for migration {migration_id}")

            if migration_record.database_type == DatabaseType.MONGODB:
                success, message = self._rollback_mongodb_migration(
                    connection_params, migration_record.from_version, migration_record.to_version
                )
            else:
                success, message = self._rollback_sql_migration(
                    migration_record.database_type, connection_params,
                    migration_record.from_version, migration_record.to_version
                )

            if success:
                migration_record.status = MigrationStatus.ROLLED_BACK
                logger.info(f"Migration {migration_id} rolled back successfully")
                return True, message
            else:
                logger.error(f"Rollback failed for migration {migration_id}: {message}")
                return False, message

        except Exception as e:
            error_msg = f"Rollback execution failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def get_migration_status(self, migration_id: str) -> Optional[MigrationRecord]:
        """Get migration status by ID."""
        return self.migration_records.get(migration_id)

    def list_migrations(self, db_type: DatabaseType = None) -> List[MigrationRecord]:
        """List all migration records, optionally filtered by database type."""
        migrations = list(self.migration_records.values())

        if db_type:
            migrations = [m for m in migrations if m.database_type == db_type]

        return sorted(migrations, key=lambda x: x.started_at, reverse=True)

    def get_available_migrations(self, db_type: DatabaseType) -> List[str]:
        """Get list of available migration scripts for a database type."""
        db_migrations_path = self.migrations_path / db_type.value

        if not db_migrations_path.exists():
            return []

        migrations = []
        for migration_file in db_migrations_path.glob("migrate_*.sql" if db_type != DatabaseType.MONGODB else "migrate_*.json"):
            migrations.append(migration_file.stem)

        return sorted(migrations)

    def _execute_sql_migration(self, db_type: DatabaseType,
                              connection_params: Dict[str, Any],
                              from_version: str, to_version: str) -> Tuple[bool, str]:
        """Execute SQL migration script."""
        try:
            migration_file = self.migrations_path / db_type.value / f"migrate_{from_version}_to_{to_version}.sql"

            if not migration_file.exists():
                return False, f"Migration script not found: {migration_file}"

            migration_sql = migration_file.read_text(encoding='utf-8')

            if db_type == DatabaseType.MYSQL:
                return self._execute_mysql_migration(connection_params, migration_sql)
            elif db_type == DatabaseType.POSTGRESQL:
                return self._execute_postgresql_migration(connection_params, migration_sql)
            elif db_type == DatabaseType.SQLITE:
                return self._execute_sqlite_migration(connection_params, migration_sql)
            else:
                return False, f"Unsupported database type: {db_type}"

        except Exception as e:
            return False, f"SQL migration execution failed: {str(e)}"

    def _execute_mongodb_migration(self, connection_params: Dict[str, Any],
                                  from_version: str, to_version: str) -> Tuple[bool, str]:
        """Execute MongoDB migration script."""
        try:
            migration_file = self.migrations_path / "mongodb" / f"migrate_{from_version}_to_{to_version}.json"

            if not migration_file.exists():
                return False, f"Migration script not found: {migration_file}"

            with open(migration_file, 'r', encoding='utf-8') as f:
                migration_data = json.load(f)

            client = pymongo.MongoClient(connection_params['uri'])
            db = client[connection_params['database']]

            # Execute migration steps
            steps = migration_data.get('steps', [])
            executed_steps = 0

            for step in steps:
                try:
                    self._execute_mongodb_step(db, step)
                    executed_steps += 1
                    logger.debug(f"Executed migration step {step['step']}: {step['description']}")
                except Exception as e:
                    logger.error(f"Failed at step {step['step']}: {str(e)}")
                    # Attempt rollback of completed steps
                    self._rollback_mongodb_steps(db, migration_data, executed_steps)
                    return False, f"Migration failed at step {step['step']}: {str(e)}"

            client.close()
            return True, f"Successfully executed {executed_steps} migration steps"

        except Exception as e:
            return False, f"MongoDB migration execution failed: {str(e)}"

    def _execute_mysql_migration(self, connection_params: Dict[str, Any],
                                migration_sql: str) -> Tuple[bool, str]:
        """Execute MySQL migration."""
        try:
            conn = mysql.connector.connect(**connection_params)
            cursor = conn.cursor()

            # Split and execute statements
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
            executed_statements = 0

            for statement in statements:
                if statement and not statement.startswith('--'):
                    cursor.execute(statement)
                    executed_statements += 1

            conn.commit()
            cursor.close()
            conn.close()

            return True, f"Successfully executed {executed_statements} SQL statements"

        except Exception as e:
            return False, f"MySQL migration failed: {str(e)}"

    def _execute_postgresql_migration(self, connection_params: Dict[str, Any],
                                    migration_sql: str) -> Tuple[bool, str]:
        """Execute PostgreSQL migration."""
        try:
            conn = psycopg2.connect(**connection_params)
            cursor = conn.cursor()

            # Execute the entire script
            cursor.execute(migration_sql)
            conn.commit()
            cursor.close()
            conn.close()

            return True, "PostgreSQL migration executed successfully"

        except Exception as e:
            return False, f"PostgreSQL migration failed: {str(e)}"

    def _execute_sqlite_migration(self, connection_params: Dict[str, Any],
                                 migration_sql: str) -> Tuple[bool, str]:
        """Execute SQLite migration."""
        try:
            db_path = connection_params.get('database', 'database.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Execute script
            cursor.executescript(migration_sql)
            conn.commit()
            conn.close()

            return True, "SQLite migration executed successfully"

        except Exception as e:
            return False, f"SQLite migration failed: {str(e)}"

    def _execute_mongodb_step(self, db, step: Dict[str, Any]):
        """Execute a single MongoDB migration step."""
        command = step.get('command')
        if not command:
            return

        collection_name = command.get('collection')
        operation = command.get('operation')

        if operation == 'createCollection':
            if collection_name not in db.list_collection_names():
                validator = command.get('validator')
                if validator:
                    db.create_collection(collection_name, validator=validator)
                else:
                    db.create_collection(collection_name)

                # Create indexes
                indexes = command.get('indexes', [])
                for index_config in indexes:
                    collection = db[collection_name]
                    collection.create_index(
                        list(index_config['key'].items()),
                        name=index_config['name'],
                        unique=index_config.get('unique', False)
                    )

        elif operation == 'updateOne':
            collection = db[collection_name]
            collection.update_one(
                command.get('filter', {}),
                command.get('update', {})
            )

        elif operation == 'updateMany':
            collection = db[collection_name]
            collection.update_many(
                command.get('filter', {}),
                command.get('update', {})
            )

        elif operation == 'insertOne':
            collection = db[collection_name]
            collection.insert_one(command.get('document', {}))

        elif operation == 'insertMany':
            collection = db[collection_name]
            documents = command.get('documents', [])
            if documents:
                collection.insert_many(documents)

        elif operation == 'createIndex':
            collection = db[collection_name]
            index_spec = command.get('index', {})
            index_name = command.get('name')
            collection.create_index(
                list(index_spec.items()),
                name=index_name,
                unique=command.get('unique', False)
            )

    def _rollback_sql_migration(self, db_type: DatabaseType,
                               connection_params: Dict[str, Any],
                               from_version: str, to_version: str) -> Tuple[bool, str]:
        """Rollback SQL migration."""
        # In a production system, you would have explicit rollback scripts
        # For now, we'll return a placeholder implementation
        logger.info(f"Rollback not implemented for SQL migrations yet")
        return False, "Rollback not implemented for SQL migrations"

    def _rollback_mongodb_migration(self, connection_params: Dict[str, Any],
                                   from_version: str, to_version: str) -> Tuple[bool, str]:
        """Rollback MongoDB migration."""
        try:
            migration_file = self.migrations_path / "mongodb" / f"migrate_{from_version}_to_{to_version}.json"

            with open(migration_file, 'r', encoding='utf-8') as f:
                migration_data = json.load(f)

            client = pymongo.MongoClient(connection_params['uri'])
            db = client[connection_params['database']]

            # Execute rollback steps
            rollback_steps = migration_data.get('rollback_steps', [])
            self._rollback_mongodb_steps(db, {"rollback_steps": rollback_steps}, len(rollback_steps))

            client.close()
            return True, f"Successfully executed {len(rollback_steps)} rollback steps"

        except Exception as e:
            return False, f"MongoDB rollback failed: {str(e)}"

    def _rollback_mongodb_steps(self, db, migration_data: Dict[str, Any], steps_count: int):
        """Rollback MongoDB migration steps."""
        rollback_steps = migration_data.get('rollback_steps', [])[:steps_count]

        for step in reversed(rollback_steps):
            try:
                commands = step.get('commands', [step.get('command')])
                for command in commands:
                    if command:
                        self._execute_mongodb_rollback_command(db, command)
            except Exception as e:
                logger.warning(f"Rollback step failed: {str(e)}")

    def _execute_mongodb_rollback_command(self, db, command: Dict[str, Any]):
        """Execute a MongoDB rollback command."""
        collection_name = command.get('collection')
        operation = command.get('operation')

        if operation == 'drop':
            if collection_name in db.list_collection_names():
                db[collection_name].drop()

        elif operation == 'updateMany':
            collection = db[collection_name]
            collection.update_many(
                command.get('filter', {}),
                command.get('update', {})
            )

        elif operation == 'deleteOne':
            collection = db[collection_name]
            collection.delete_one(command.get('filter', {}))

        elif operation == 'deleteMany':
            collection = db[collection_name]
            collection.delete_many(command.get('filter', {}))

    def _run_pre_migration_checks(self, db_type: DatabaseType,
                                 connection_params: Dict[str, Any],
                                 current_version: str) -> bool:
        """Run pre-migration validation checks."""
        try:
            # Check database connectivity
            if not self._test_connection(db_type, connection_params):
                logger.error("Database connection test failed")
                return False

            # Verify current schema version
            actual_version = self._get_current_schema_version(db_type, connection_params)
            if actual_version != current_version:
                logger.error(f"Schema version mismatch: expected {current_version}, found {actual_version}")
                return False

            # Check for sufficient disk space (placeholder)
            # In production, implement actual disk space check

            logger.info("Pre-migration checks passed")
            return True

        except Exception as e:
            logger.error(f"Pre-migration checks failed: {str(e)}")
            return False

    def _run_post_migration_checks(self, db_type: DatabaseType,
                                  connection_params: Dict[str, Any],
                                  target_version: str) -> bool:
        """Run post-migration validation checks."""
        try:
            # Verify schema version updated
            actual_version = self._get_current_schema_version(db_type, connection_params)
            if actual_version != target_version:
                logger.error(f"Schema version not updated: expected {target_version}, found {actual_version}")
                return False

            # Test basic functionality (placeholder)
            # In production, implement comprehensive functionality tests

            logger.info("Post-migration checks passed")
            return True

        except Exception as e:
            logger.error(f"Post-migration checks failed: {str(e)}")
            return False

    def _test_connection(self, db_type: DatabaseType,
                        connection_params: Dict[str, Any]) -> bool:
        """Test database connection."""
        try:
            if db_type == DatabaseType.MYSQL:
                conn = mysql.connector.connect(**connection_params)
                conn.close()
            elif db_type == DatabaseType.POSTGRESQL:
                conn = psycopg2.connect(**connection_params)
                conn.close()
            elif db_type == DatabaseType.SQLITE:
                db_path = connection_params.get('database', 'database.db')
                conn = sqlite3.connect(db_path)
                conn.close()
            elif db_type == DatabaseType.MONGODB:
                client = pymongo.MongoClient(connection_params['uri'])
                client.server_info()
                client.close()

            return True
        except Exception:
            return False

    def _get_current_schema_version(self, db_type: DatabaseType,
                                   connection_params: Dict[str, Any]) -> Optional[str]:
        """Get current schema version from database."""
        try:
            if db_type == DatabaseType.MONGODB:
                client = pymongo.MongoClient(connection_params['uri'])
                db = client[connection_params['database']]

                result = db.schema_info.find_one(
                    {"database_type": "mongodb"},
                    sort=[("created_at", -1)]
                )
                client.close()

                return result.get('schema_version') if result else None
            else:
                # SQL databases
                query = "SELECT schema_version FROM schema_info WHERE database_type = %s ORDER BY created_at DESC LIMIT 1"

                if db_type == DatabaseType.MYSQL:
                    conn = mysql.connector.connect(**connection_params)
                    cursor = conn.cursor()
                    cursor.execute(query, (db_type.value,))
                    result = cursor.fetchone()
                    cursor.close()
                    conn.close()
                    return result[0] if result else None

                elif db_type == DatabaseType.POSTGRESQL:
                    conn = psycopg2.connect(**connection_params)
                    cursor = conn.cursor()
                    cursor.execute(query, (db_type.value,))
                    result = cursor.fetchone()
                    cursor.close()
                    conn.close()
                    return result[0] if result else None

                elif db_type == DatabaseType.SQLITE:
                    db_path = connection_params.get('database', 'database.db')
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute(query.replace('%s', '?'), (db_type.value,))
                    result = cursor.fetchone()
                    cursor.close()
                    conn.close()
                    return result[0] if result else None

        except Exception as e:
            logger.error(f"Failed to get current schema version: {str(e)}")
            return None