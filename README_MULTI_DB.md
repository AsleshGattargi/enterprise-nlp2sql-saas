# Multi-Tenant NLP2SQL with Multiple Database Types

This project now supports **different database types for each organization**, providing true multi-tenant isolation and demonstrating real-world database diversity.

## 🏗️ Architecture Overview

### Organization Database Mapping

| Organization | Database Type | Port | Admin Tool | Sample Domain |
|-------------|---------------|------|------------|---------------|
| **TechCorp** (org-001) | SQLite | File-based | N/A | @techcorp.com |
| **HealthPlus** (org-002) | MySQL | 3307 | phpMyAdmin (8080) | @healthplus.org |
| **FinanceHub** (org-003) | PostgreSQL | 5433 | pgAdmin (8081) | @financehub.net |
| **RetailMax** (org-004) | MongoDB | 27018 | Mongo Express (8082) | @retailmax.com |
| **EduLearn** (org-005) | MySQL | 3308 | phpMyAdmin | @edulearn.edu |

### System Components

- **FastAPI Backend**: Multi-database connection management with dialect-aware SQL generation
- **Streamlit Frontend**: Organization-specific UI with database type indicators
- **Docker Services**: Containerized databases with persistent storage
- **Database Admin Tools**: Web-based administration for each database type

## 🚀 Quick Start

### Option 1: Docker Mode (Recommended)

Start the complete multi-database system:

```bash
# Clone and navigate to project
cd "Multi Tenant NLP2SQL"

# Start all services with Docker
python start_multi_db_system.py docker
```

This will:
- ✅ Start all database containers (MySQL, PostgreSQL, MongoDB)
- ✅ Initialize databases with sample data
- ✅ Start the NLP2SQL application
- ✅ Provide database admin tools

### Option 2: Local Development Mode

For development without Docker:

```bash
# Start with SQLite fallbacks
python start_multi_db_system.py local
```

### Option 3: Health Check

Check system status and database connections:

```bash
python start_multi_db_system.py check
```

## 📊 Database Schemas

### TechCorp (SQLite)
```sql
-- Technology company with products and sales
Tables: products, sales, employees, inventory
Sample Data: Laptops, accessories, tech equipment
```

### HealthPlus (MySQL)
```sql
-- Healthcare organization
Tables: patients, doctors, treatments, appointments, medical_records
Sample Data: Patient records, medical appointments, treatments
```

### FinanceHub (PostgreSQL)
```sql
-- Financial services company
Tables: accounts, transactions, loans, investments, credit_cards
Sample Data: Banking transactions, investment portfolios, loan data
```

### RetailMax (MongoDB)
```javascript
// E-commerce retail company
Collections: products, customers, orders, sales_analytics, inventory_movements
Sample Data: Product catalog, customer orders, sales analytics
```

### EduLearn (MySQL)
```sql
-- Educational institution
Tables: students, instructors, courses, course_sections, enrollments, grades
Sample Data: Student records, course enrollments, academic grades
```

## 🔐 Sample Login Credentials

### Admin Users (Full Access)
```
TechCorp:     diana.rodriguez0@techcorp.com / password123
HealthPlus:   dr.rodriguez50@healthplus.org / password123
FinanceHub:   cfo.rodriguez100@financehub.net / password123
RetailMax:    ceo.rodriguez150@retailmax.com / password123
EduLearn:     dean.rodriguez200@edulearn.edu / password123
```

### Additional Users
Each organization has 50 users with different roles:
- 1 Admin, 4 Managers, 10 Analysts, 10 Developers, 25 Viewers

## 🌐 Service URLs

### Application Services
- **Streamlit Frontend**: http://localhost:8501
- **FastAPI Backend**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs

### Database Admin Tools (Docker Mode)
- **phpMyAdmin** (HealthPlus MySQL): http://localhost:8080
- **pgAdmin** (FinanceHub PostgreSQL): http://localhost:8081
- **Mongo Express** (RetailMax): http://localhost:8082

### Direct Database Connections
```bash
# HealthPlus MySQL
mysql -h localhost -P 3307 -u healthplus_user -p healthplus_db

# FinanceHub PostgreSQL
psql -h localhost -p 5433 -U financehub_user -d financehub_db

# RetailMax MongoDB
mongo mongodb://retailmax_admin:retailmax_pass_2024@localhost:27018/retailmax_db

# EduLearn MySQL
mysql -h localhost -P 3308 -u edulearn_user -p edulearn_db

# TechCorp SQLite
sqlite3 databases/techcorp_db.sqlite
```

## 💻 Development Setup

### Environment Configuration

1. Copy environment template:
```bash
cp .env.example .env
```

2. Update database credentials in `.env`:
```bash
# Organization-specific database configurations
HEALTHPLUS_DB_PASSWORD=your_secure_password
FINANCEHUB_DB_PASSWORD=your_secure_password
RETAILMAX_DB_PASSWORD=your_secure_password
EDULEARN_DB_PASSWORD=your_secure_password
```

### Manual Database Setup

If you prefer manual database setup:

1. **MySQL Databases** (HealthPlus & EduLearn):
```bash
docker run -d --name healthplus_mysql \
  -e MYSQL_ROOT_PASSWORD=healthplus_root_2024 \
  -e MYSQL_DATABASE=healthplus_db \
  -e MYSQL_USER=healthplus_user \
  -e MYSQL_PASSWORD=healthplus_pass_2024 \
  -p 3307:3306 mysql:8.0
```

2. **PostgreSQL Database** (FinanceHub):
```bash
docker run -d --name financehub_postgres \
  -e POSTGRES_DB=financehub_db \
  -e POSTGRES_USER=financehub_user \
  -e POSTGRES_PASSWORD=financehub_pass_2024 \
  -p 5433:5432 postgres:15
```

3. **MongoDB Database** (RetailMax):
```bash
docker run -d --name retailmax_mongo \
  -e MONGO_INITDB_ROOT_USERNAME=retailmax_admin \
  -e MONGO_INITDB_ROOT_PASSWORD=retailmax_pass_2024 \
  -p 27018:27017 mongo:7.0
```

## 🔧 Configuration Files

### Docker Compose
- `docker-compose.yml`: Complete multi-database setup
- Database initialization scripts in `database/` folders
- Persistent volumes for data retention

### Database Initialization
```
database/
├── healthplus/init.sql      # MySQL healthcare schema
├── financehub/init.sql      # PostgreSQL financial schema
├── retailmax/init.js        # MongoDB retail collections
├── edulearn/init.sql        # MySQL education schema
└── techcorp/sample_data.sql # SQLite tech company data
```

## 🎯 Features Demonstrated

### Multi-Database Support
- ✅ **SQLite**: File-based, perfect for small organizations
- ✅ **MySQL**: Robust relational database for healthcare/education
- ✅ **PostgreSQL**: Advanced SQL features for financial services
- ✅ **MongoDB**: Document-based for e-commerce product catalogs

### Organization-Specific Features
- **Database Type Detection**: UI shows which database type each org uses
- **Dialect-Aware SQL**: Generates database-specific SQL syntax
- **Schema Isolation**: Each organization has completely separate schemas
- **Sample Data**: Realistic data tailored to each industry

### Query Capabilities
```sql
-- TechCorp (SQLite): Simple product queries
"Show me all products in the Electronics category"

-- HealthPlus (MySQL): Healthcare analytics
"How many patients were treated this month?"

-- FinanceHub (PostgreSQL): Financial analysis
"What's the total value of all investment accounts?"

-- RetailMax (MongoDB): E-commerce insights
"Show me the top-selling products by category"

-- EduLearn (MySQL): Academic reporting
"What's the average GPA by department?"
```

## 🛠️ Troubleshooting

### Common Issues

1. **Port Conflicts**: Check if ports 3307, 5433, 27018, 8080-8082 are available
2. **Docker Issues**: Ensure Docker and Docker Compose are installed
3. **Database Connection**: Verify environment variables in `.env`
4. **Disk Space**: Docker images and data volumes require ~2GB

### Health Check Commands
```bash
# Check all database connections
python start_multi_db_system.py check

# View Docker container status
docker-compose ps

# Check specific database logs
docker-compose logs healthplus-mysql
docker-compose logs financehub-postgres
docker-compose logs retailmax-mongo
```

### Reset Databases
```bash
# Stop and remove all containers with data
docker-compose down -v

# Restart fresh
python start_multi_db_system.py docker
```

## 📈 Scaling and Production

### Production Considerations
- Use proper SSL certificates for database connections
- Implement connection pooling for high-traffic scenarios
- Set up database replication for critical organizations
- Monitor database performance and query execution times

### Adding New Organizations
1. Add database configuration to `docker-compose.yml`
2. Create initialization script in `database/new_org/`
3. Update environment variables
4. Add organization mapping in `src/database.py`

## 🤝 Contributing

When adding new database types or organizations:
1. Update the database connection logic in `src/database.py`
2. Add initialization scripts in `database/org_name/`
3. Update Docker configuration
4. Add sample login credentials
5. Test with `python start_multi_db_system.py check`

## 📝 License

This project demonstrates multi-tenant architecture patterns and is provided for educational purposes.