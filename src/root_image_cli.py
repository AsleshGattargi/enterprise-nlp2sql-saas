#!/usr/bin/env python3
"""
CLI Tool for Root Database Image Management
Multi-Tenant NLP2SQL System
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any

from root_image_manager import RootImageManager, DatabaseType
from schema_version_manager import SchemaVersionManager
from migration_manager import MigrationManager
from root_schemas.validators.schema_validator import SchemaValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RootImageCLI:
    """Command-line interface for Root Image Management."""

    def __init__(self):
        self.root_manager = RootImageManager()
        self.version_manager = SchemaVersionManager()
        self.migration_manager = MigrationManager()
        self.validator = SchemaValidator()

    def create_schema(self, args):
        """Create a new root schema."""
        try:
            db_type = DatabaseType(args.db_type.lower())

            # Load connection parameters
            if args.config:
                with open(args.config, 'r') as f:
                    connection_params = json.load(f)
            else:
                connection_params = self._get_connection_params_interactive(db_type)

            logger.info(f"Creating root schema for {db_type.value}")

            success = self.root_manager.create_root_schema(
                db_type=db_type,
                connection_params=connection_params,
                version=args.version,
                force=args.force
            )

            if success:
                print(f"✅ Root schema created successfully for {db_type.value}")
                return 0
            else:
                print(f"❌ Failed to create root schema for {db_type.value}")
                return 1

        except Exception as e:
            logger.error(f"Error creating schema: {e}")
            print(f"❌ Error: {e}")
            return 1

    def validate_schema(self, args):
        """Validate a schema definition."""
        try:
            db_type = DatabaseType(args.db_type.lower())

            # Get schema content
            if args.file:
                schema_content = Path(args.file).read_text(encoding='utf-8')
            else:
                schema_content = self.root_manager.get_schema_content(db_type, args.version)
                if not schema_content:
                    print(f"❌ Schema not found for {db_type.value} version {args.version}")
                    return 1

            logger.info(f"Validating schema for {db_type.value}")

            result = self.validator.validate_schema(schema_content, db_type.value)

            # Print validation results
            self._print_validation_results(result)

            return 0 if result.is_valid else 1

        except Exception as e:
            logger.error(f"Error validating schema: {e}")
            print(f"❌ Error: {e}")
            return 1

    def migrate_schema(self, args):
        """Execute schema migration."""
        try:
            db_type = DatabaseType(args.db_type.lower())

            # Load connection parameters
            if args.config:
                with open(args.config, 'r') as f:
                    connection_params = json.load(f)
            else:
                connection_params = self._get_connection_params_interactive(db_type)

            logger.info(f"Migrating {db_type.value} from {args.from_version} to {args.to_version}")

            success, message = self.migration_manager.execute_migration(
                from_version=args.from_version,
                to_version=args.to_version,
                db_type=db_type,
                connection_params=connection_params,
                dry_run=args.dry_run
            )

            if success:
                print(f"✅ Migration completed: {message}")
                return 0
            else:
                print(f"❌ Migration failed: {message}")
                return 1

        except Exception as e:
            logger.error(f"Error during migration: {e}")
            print(f"❌ Error: {e}")
            return 1

    def list_versions(self, args):
        """List available schema versions."""
        try:
            if args.db_type:
                db_type = DatabaseType(args.db_type.lower())
                versions = self.root_manager.get_available_versions(db_type)

                print(f"\n📋 Available versions for {db_type.value}:")
                for version in versions:
                    print(f"  • {version.version} - {version.description}")
                    print(f"    Created: {version.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                # List all versions for all database types
                for db_type in DatabaseType:
                    versions = self.root_manager.get_available_versions(db_type)
                    if versions:
                        print(f"\n📋 {db_type.value.upper()} versions:")
                        for version in versions:
                            print(f"  • {version.version} - {version.description}")

            return 0

        except Exception as e:
            logger.error(f"Error listing versions: {e}")
            print(f"❌ Error: {e}")
            return 1

    def show_migration_status(self, args):
        """Show migration status."""
        try:
            if args.migration_id:
                # Show specific migration
                migration = self.migration_manager.get_migration_status(args.migration_id)
                if migration:
                    self._print_migration_details(migration)
                else:
                    print(f"❌ Migration not found: {args.migration_id}")
                    return 1
            else:
                # List all migrations
                db_type = DatabaseType(args.db_type.lower()) if args.db_type else None
                migrations = self.migration_manager.list_migrations(db_type)

                if not migrations:
                    print("📋 No migrations found")
                    return 0

                print("\n📋 Migration History:")
                for migration in migrations:
                    status_icon = self._get_status_icon(migration.status)
                    print(f"  {status_icon} {migration.migration_id}")
                    print(f"    {migration.from_version} → {migration.to_version} ({migration.database_type.value})")
                    print(f"    Started: {migration.started_at.strftime('%Y-%m-%d %H:%M:%S')}")

                    if migration.completed_at:
                        print(f"    Completed: {migration.completed_at.strftime('%Y-%m-%d %H:%M:%S')}")

                    if migration.error_message:
                        print(f"    Error: {migration.error_message}")
                    print()

            return 0

        except Exception as e:
            logger.error(f"Error showing migration status: {e}")
            print(f"❌ Error: {e}")
            return 1

    def backup_schema(self, args):
        """Create schema backup."""
        try:
            db_type = DatabaseType(args.db_type.lower())

            # Load connection parameters
            if args.config:
                with open(args.config, 'r') as f:
                    connection_params = json.load(f)
            else:
                connection_params = self._get_connection_params_interactive(db_type)

            logger.info(f"Creating backup for {db_type.value}")

            backup_path = self.root_manager.backup_schema(
                db_type=db_type,
                connection_params=connection_params,
                backup_path=args.output
            )

            if backup_path:
                print(f"✅ Backup created: {backup_path}")
                return 0
            else:
                print("❌ Backup failed")
                return 1

        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            print(f"❌ Error: {e}")
            return 1

    def _get_connection_params_interactive(self, db_type: DatabaseType) -> Dict[str, Any]:
        """Get connection parameters interactively."""
        print(f"\n🔗 Enter connection parameters for {db_type.value}:")

        if db_type == DatabaseType.MYSQL:
            return {
                'host': input("Host (localhost): ") or 'localhost',
                'port': int(input("Port (3306): ") or '3306'),
                'user': input("Username: "),
                'password': input("Password: "),
                'database': input("Database name: ")
            }
        elif db_type == DatabaseType.POSTGRESQL:
            return {
                'host': input("Host (localhost): ") or 'localhost',
                'port': int(input("Port (5432): ") or '5432'),
                'user': input("Username: "),
                'password': input("Password: "),
                'database': input("Database name: ")
            }
        elif db_type == DatabaseType.SQLITE:
            return {
                'database': input("Database file path: ")
            }
        elif db_type == DatabaseType.MONGODB:
            return {
                'uri': input("MongoDB URI: "),
                'database': input("Database name: ")
            }

    def _print_validation_results(self, result):
        """Print schema validation results."""
        print(f"\n📊 Validation Results:")
        print(f"Score: {result.score:.1f}/100")
        print(f"Status: {'✅ Valid' if result.is_valid else '❌ Invalid'}")

        if result.issues:
            print(f"\n🔍 Issues ({len(result.issues)}):")
            for issue in result.issues:
                severity_icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}[issue.severity.value]
                print(f"  {severity_icon} {issue.message}")
                if issue.table:
                    print(f"      Table: {issue.table}")
                if issue.column:
                    print(f"      Column: {issue.column}")

        if result.performance_warnings:
            print(f"\n⚡ Performance Warnings ({len(result.performance_warnings)}):")
            for warning in result.performance_warnings:
                print(f"  ⚠️ {warning}")

        if result.security_warnings:
            print(f"\n🔒 Security Warnings ({len(result.security_warnings)}):")
            for warning in result.security_warnings:
                print(f"  ⚠️ {warning}")

        if result.compliance_issues:
            print(f"\n📋 Compliance Issues ({len(result.compliance_issues)}):")
            for issue in result.compliance_issues:
                print(f"  ⚠️ {issue}")

    def _print_migration_details(self, migration):
        """Print detailed migration information."""
        status_icon = self._get_status_icon(migration.status)

        print(f"\n📋 Migration Details:")
        print(f"ID: {migration.migration_id}")
        print(f"Status: {status_icon} {migration.status.value}")
        print(f"Database: {migration.database_type.value}")
        print(f"Version: {migration.from_version} → {migration.to_version}")
        print(f"Started: {migration.started_at.strftime('%Y-%m-%d %H:%M:%S')}")

        if migration.completed_at:
            duration = migration.completed_at - migration.started_at
            print(f"Completed: {migration.completed_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Duration: {duration.total_seconds():.1f} seconds")

        if migration.error_message:
            print(f"Error: {migration.error_message}")

        print(f"Rollback Available: {'✅' if migration.rollback_available else '❌'}")

    def _get_status_icon(self, status):
        """Get icon for migration status."""
        icons = {
            "pending": "⏳",
            "in_progress": "🔄",
            "completed": "✅",
            "failed": "❌",
            "rolled_back": "↩️"
        }
        return icons.get(status.value, "❓")

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Root Database Image Management CLI")
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Create schema command
    create_parser = subparsers.add_parser('create', help='Create root schema')
    create_parser.add_argument('db_type', choices=['mysql', 'postgresql', 'sqlite', 'mongodb'],
                              help='Database type')
    create_parser.add_argument('--version', help='Schema version to use (default: latest)')
    create_parser.add_argument('--config', help='JSON file with connection parameters')
    create_parser.add_argument('--force', action='store_true', help='Force creation even if schema exists')

    # Validate schema command
    validate_parser = subparsers.add_parser('validate', help='Validate schema')
    validate_parser.add_argument('db_type', choices=['mysql', 'postgresql', 'sqlite', 'mongodb'],
                                help='Database type')
    validate_parser.add_argument('--version', help='Schema version to validate (default: latest)')
    validate_parser.add_argument('--file', help='Schema file to validate instead of version')

    # Migrate schema command
    migrate_parser = subparsers.add_parser('migrate', help='Migrate schema')
    migrate_parser.add_argument('db_type', choices=['mysql', 'postgresql', 'sqlite', 'mongodb'],
                               help='Database type')
    migrate_parser.add_argument('from_version', help='Source version')
    migrate_parser.add_argument('to_version', help='Target version')
    migrate_parser.add_argument('--config', help='JSON file with connection parameters')
    migrate_parser.add_argument('--dry-run', action='store_true', help='Validate migration without executing')

    # List versions command
    list_parser = subparsers.add_parser('list', help='List available versions')
    list_parser.add_argument('--db-type', choices=['mysql', 'postgresql', 'sqlite', 'mongodb'],
                            help='Filter by database type')

    # Migration status command
    status_parser = subparsers.add_parser('status', help='Show migration status')
    status_parser.add_argument('--migration-id', help='Specific migration ID')
    status_parser.add_argument('--db-type', choices=['mysql', 'postgresql', 'sqlite', 'mongodb'],
                              help='Filter by database type')

    # Backup schema command
    backup_parser = subparsers.add_parser('backup', help='Create schema backup')
    backup_parser.add_argument('db_type', choices=['mysql', 'postgresql', 'sqlite', 'mongodb'],
                              help='Database type')
    backup_parser.add_argument('--config', help='JSON file with connection parameters')
    backup_parser.add_argument('--output', help='Output backup file path')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if not args.command:
        parser.print_help()
        return 1

    cli = RootImageCLI()

    # Execute command
    if args.command == 'create':
        return cli.create_schema(args)
    elif args.command == 'validate':
        return cli.validate_schema(args)
    elif args.command == 'migrate':
        return cli.migrate_schema(args)
    elif args.command == 'list':
        return cli.list_versions(args)
    elif args.command == 'status':
        return cli.show_migration_status(args)
    elif args.command == 'backup':
        return cli.backup_schema(args)
    else:
        parser.print_help()
        return 1

if __name__ == '__main__':
    sys.exit(main())