# Root Database Image System
## Multi-Tenant NLP2SQL Schema Management

A comprehensive system for managing root database schemas, versioning, and migrations across multiple database types in a multi-tenant environment.

## 🌟 Features

- **Multi-Database Support**: MySQL, PostgreSQL, SQLite, MongoDB
- **Schema Versioning**: Complete version control and compatibility tracking
- **Migration Management**: Automated schema upgrades with rollback support
- **Validation System**: Comprehensive schema validation for integrity, performance, and security
- **CLI Tools**: Command-line interface for all operations
- **Enterprise Ready**: Designed for production multi-tenant environments

## 📁 Directory Structure

```
root_schemas/
├── mysql/
│   ├── v1.0/
│   │   └── root_schema.sql
│   └── v1.1/
├── postgresql/
│   ├── v1.0/
│   │   └── root_schema.sql
│   └── v1.1/
├── sqlite/
│   ├── v1.0/
│   │   └── root_schema.sql
│   └── v1.1/
├── mongodb/
│   ├── v1.0/
│   │   └── root_schema.json
│   └── v1.1/
├── migrations/
│   ├── mysql/
│   │   └── migrate_v1.0_to_v1.1.sql
│   ├── postgresql/
│   │   └── migrate_v1.0_to_v1.1.sql
│   ├── sqlite/
│   │   └── migrate_v1.0_to_v1.1.sql
│   └── mongodb/
│       └── migrate_v1.0_to_v1.1.json
├── validators/
│   └── schema_validator.py
├── schema_versions.json
└── README.md

src/
├── root_image_manager.py
├── schema_version_manager.py
├── migration_manager.py
└── root_image_cli.py
```

## 🚀 Quick Start

### 1. Installation

```bash
# Install required dependencies
pip install -r requirements.txt

# Make CLI executable
chmod +x src/root_image_cli.py
```

### 2. Create Your First Root Schema

```bash
# For MySQL
python src/root_image_cli.py create mysql --config mysql_config.json

# For PostgreSQL
python src/root_image_cli.py create postgresql --config postgres_config.json

# For SQLite (interactive)
python src/root_image_cli.py create sqlite

# For MongoDB
python src/root_image_cli.py create mongodb --config mongo_config.json
```

### 3. Connection Configuration Files

**MySQL Configuration (mysql_config.json):**
```json
{
  "host": "localhost",
  "port": 3306,
  "user": "root",
  "password": "your_password",
  "database": "nlp2sql_metadata"
}
```

**PostgreSQL Configuration (postgres_config.json):**
```json
{
  "host": "localhost",
  "port": 5432,
  "user": "postgres",
  "password": "your_password",
  "database": "nlp2sql_metadata"
}
```

**MongoDB Configuration (mongo_config.json):**
```json
{
  "uri": "mongodb://localhost:27017",
  "database": "nlp2sql_metadata"
}
```

## 🔧 Core Components

### 1. Root Image Manager

Manages master schema templates and database creation:

```python
from src.root_image_manager import RootImageManager, DatabaseType

# Initialize manager
rim = RootImageManager()

# Create schema
success = rim.create_root_schema(
    db_type=DatabaseType.MYSQL,
    connection_params={
        'host': 'localhost',
        'user': 'root',
        'password': 'password',
        'database': 'my_db'
    }
)

# Validate schema
result = rim.validate_schema(DatabaseType.MYSQL)
print(f"Schema valid: {result.is_valid}")

# Get available versions
versions = rim.get_available_versions(DatabaseType.MYSQL)
for version in versions:
    print(f"Version {version.version}: {version.description}")
```

### 2. Schema Version Manager

Handles version control and compatibility:

```python
from src.schema_version_manager import SchemaVersionManager

svm = SchemaVersionManager()

# Check compatibility
is_compatible, message = svm.check_database_compatibility(
    version='v1.0',
    db_type='mysql',
    db_version='8.0'
)

# Get upgrade path
upgrade_path = svm.get_upgrade_path('v1.0', 'v1.1')
if upgrade_path and upgrade_path.supported:
    print(f"Upgrade available: {upgrade_path.description}")
```

### 3. Migration Manager

Executes schema migrations with rollback support:

```python
from src.migration_manager import MigrationManager

mm = MigrationManager()

# Execute migration
success, message = mm.execute_migration(
    from_version='v1.0',
    to_version='v1.1',
    db_type=DatabaseType.MYSQL,
    connection_params=mysql_params
)

# Check migration status
migration = mm.get_migration_status(migration_id)
print(f"Migration status: {migration.status}")

# Rollback if needed
if migration.rollback_available:
    success, message = mm.rollback_migration(migration_id, mysql_params)
```

### 4. Schema Validator

Comprehensive validation system:

```python
from root_schemas.validators.schema_validator import SchemaValidator

validator = SchemaValidator()

# Validate schema
result = validator.validate_schema(schema_content, 'mysql')

print(f"Validation Score: {result.score}/100")
print(f"Issues: {len(result.issues)}")
print(f"Security Warnings: {len(result.security_warnings)}")
print(f"Performance Warnings: {len(result.performance_warnings)}")
```

## 📋 CLI Commands

### List Available Versions
```bash
# List all versions
python src/root_image_cli.py list

# List versions for specific database
python src/root_image_cli.py list --db-type mysql
```

### Validate Schema
```bash
# Validate latest version
python src/root_image_cli.py validate mysql

# Validate specific version
python src/root_image_cli.py validate mysql --version v1.0

# Validate external file
python src/root_image_cli.py validate mysql --file my_schema.sql
```

### Migrate Schema
```bash
# Perform migration
python src/root_image_cli.py migrate mysql v1.0 v1.1 --config mysql_config.json

# Dry run (validation only)
python src/root_image_cli.py migrate mysql v1.0 v1.1 --config mysql_config.json --dry-run
```

### Migration Status
```bash
# List all migrations
python src/root_image_cli.py status

# Check specific migration
python src/root_image_cli.py status --migration-id migration_123
```

### Create Backup
```bash
# Create backup
python src/root_image_cli.py backup mysql --config mysql_config.json --output backup.sql
```

## 🏗️ Schema Structure

### Core Tables

All database types include these essential tables:

1. **schema_info** - Version and metadata tracking
2. **organizations** - Multi-tenant organization definitions
3. **users** - User accounts within organizations
4. **hdt_profiles** - Human Digital Twin profiles
5. **hdt_agents** - AI agents for HDT systems
6. **query_logs** - Complete audit trail of NLP2SQL queries
7. **permissions** - Resource-based access control
8. **security_logs** - Security events and monitoring
9. **api_tokens** - Service authentication tokens
10. **system_settings** - Configuration management

### Database-Specific Features

**MySQL:**
- UUID generation with `UUID()` function
- JSON data types for flexible configurations
- Comprehensive indexing strategy
- Foreign key constraints with cascading

**PostgreSQL:**
- UUID extension with `uuid_generate_v4()`
- JSONB for efficient JSON operations
- Advanced indexing with partial indexes
- Trigger-based audit logging

**SQLite:**
- Custom UUID generation with `randomblob()`
- JSON as TEXT with validation
- Comprehensive constraint checking
- Trigger-based timestamp updates

**MongoDB:**
- Document validation with JSON Schema
- Compound indexes for performance
- GridFS support for large documents
- Aggregation pipeline optimizations

## 🔒 Security Features

- **Password Hashing**: All passwords stored as secure hashes
- **Audit Logging**: Complete security event tracking
- **Access Control**: Role-based permissions system
- **Token Management**: Secure API token system with expiration
- **Data Encryption**: Support for field-level encryption
- **Compliance**: GDPR and data protection features

## 📊 Performance Optimizations

- **Strategic Indexing**: Performance-critical indexes on all tables
- **Query Caching**: Built-in query result caching system
- **Connection Pooling**: Efficient database connection management
- **Batch Operations**: Optimized for bulk data operations
- **Monitoring**: Query performance tracking and optimization

## 🔄 Migration System

### Migration Features

- **Atomic Transactions**: All-or-nothing migration execution
- **Rollback Support**: Safe rollback to previous versions
- **Dry Run**: Validate migrations before execution
- **Progress Tracking**: Real-time migration status monitoring
- **Error Recovery**: Automatic cleanup on migration failures

### Migration Process

1. **Pre-validation**: Connection, version, and space checks
2. **Backup Creation**: Automatic backup before migration
3. **Migration Execution**: Step-by-step schema updates
4. **Post-validation**: Verify successful migration
5. **Cleanup**: Remove temporary files and connections

## 🧪 Testing and Validation

### Validation Categories

- **Structural**: Required tables, columns, and relationships
- **Performance**: Index coverage and query optimization
- **Security**: Access controls and encryption requirements
- **Compliance**: GDPR, data retention, and audit requirements
- **Compatibility**: Database version and feature support

### Test Coverage

- Unit tests for all core components
- Integration tests with real databases
- Performance benchmarks
- Security vulnerability scans
- Compliance validation tests

## 📈 Monitoring and Metrics

### Available Metrics

- Schema validation scores
- Migration success rates
- Performance benchmarks
- Security event counts
- Compliance status indicators

### Monitoring Integration

```python
# Custom monitoring hooks
from src.root_image_manager import RootImageManager

class MonitoredRootImageManager(RootImageManager):
    def create_root_schema(self, *args, **kwargs):
        # Your monitoring logic here
        start_time = time.time()
        result = super().create_root_schema(*args, **kwargs)
        duration = time.time() - start_time

        # Send metrics to monitoring system
        self.send_metric('schema_creation_duration', duration)
        return result
```

## 🚀 Production Deployment

### Environment Setup

1. **Database Servers**: Set up MySQL, PostgreSQL, and MongoDB instances
2. **Connection Pooling**: Configure connection pools for each database type
3. **Monitoring**: Deploy monitoring and alerting systems
4. **Backup Strategy**: Implement automated backup procedures
5. **Security**: Configure SSL/TLS and access controls

### Deployment Checklist

- [ ] Database servers configured and accessible
- [ ] Connection parameters secured (use environment variables)
- [ ] Monitoring and alerting configured
- [ ] Backup procedures tested
- [ ] Migration rollback procedures verified
- [ ] Security audit completed
- [ ] Performance benchmarks established

## 🤝 Contributing

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd multi-tenant-nlp2sql

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Run validation
python src/root_image_cli.py validate mysql
```

### Code Standards

- Follow PEP 8 style guidelines
- Include comprehensive docstrings
- Add unit tests for new features
- Update documentation for changes
- Validate all schema modifications

## 📚 Advanced Usage

### Custom Schema Extensions

```python
# Create custom schema template
custom_schema = """
CREATE TABLE custom_analytics (
    analytics_id VARCHAR(36) PRIMARY KEY,
    org_id VARCHAR(36) NOT NULL,
    metric_name VARCHAR(255),
    metric_value DECIMAL(15,4),
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (org_id) REFERENCES organizations(org_id)
);
"""

# Extend existing schema
rim = RootImageManager()
existing_schema = rim.get_schema_content(DatabaseType.MYSQL)
extended_schema = existing_schema + custom_schema

# Validate extended schema
result = rim.validate_schema(DatabaseType.MYSQL)
```

### Automated Migration Workflows

```python
# Automated upgrade workflow
def upgrade_all_tenants():
    tenants = get_tenant_list()

    for tenant in tenants:
        try:
            success, message = migration_manager.execute_migration(
                from_version='v1.0',
                to_version='v1.1',
                db_type=tenant.db_type,
                connection_params=tenant.connection_params
            )

            if not success:
                logger.error(f"Migration failed for tenant {tenant.id}: {message}")
                # Handle failure (rollback, alert, etc.)
            else:
                logger.info(f"Migration successful for tenant {tenant.id}")

        except Exception as e:
            logger.error(f"Unexpected error for tenant {tenant.id}: {e}")
```

## 🆘 Troubleshooting

### Common Issues

**Connection Failures:**
- Verify database server is running
- Check connection parameters
- Ensure network connectivity
- Validate user permissions

**Migration Failures:**
- Review migration logs
- Check database locks
- Verify sufficient disk space
- Validate schema compatibility

**Validation Errors:**
- Review validation report
- Check required dependencies
- Verify database version compatibility
- Update schema templates if needed

### Support

For support and questions:
- Check documentation in `/docs`
- Review issue tracker
- Contact system administrators
- Consult database-specific documentation

## 📄 License

This project is part of the Multi-Tenant NLP2SQL system. All rights reserved.