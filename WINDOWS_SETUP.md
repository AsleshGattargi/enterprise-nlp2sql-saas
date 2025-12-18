# Multi-Tenant NLP2SQL System - Windows Setup

## Quick Start (Windows)

### Step 1: Setup System
```cmd
python setup_windows.py
```

### Step 2: Install Dependencies
```cmd
pip install -r requirements.txt
```

### Step 3: Setup Database (requires MySQL)
```cmd
setup_databases.bat
```

### Step 4: Start System
```cmd
run_system.bat
```

## Access the Application
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000

## Sample Login Credentials

**TechCorp (@techcorp.com)**
- Admin: diana.rodriguez0@techcorp.com / password123
- Manager: john.smith1@techcorp.com / password123
- Analyst: alex.davis5@techcorp.com / password123

**HealthPlus (@healthplus.org)**
- Admin: dr.rodriguez50@healthplus.org / password123
- Analyst: anna.analyst55@healthplus.org / password123

**FinanceHub (@financehub.net)**
- Admin: cfo.rodriguez100@financehub.net / password123

**RetailMax (@retailmax.com)**
- Admin: ceo.rodriguez150@retailmax.com / password123

**EduLearn (@edulearn.edu)**
- Admin: dean.rodriguez200@edulearn.edu / password123

## System Features

- **Multi-Tenant Architecture**: 5 organizations with complete data isolation
- **250 Users Total**: 50 users per organization with role-based access
- **Natural Language Queries**: Ask questions in plain English
- **Multiple Database Support**: MySQL, PostgreSQL, MongoDB
- **Security Features**: SQL injection prevention, audit logging
- **Professional UI**: Modern web interface with data visualization

## Requirements

- Python 3.11+
- MySQL 8.0+ (required)
- PostgreSQL 15+ (optional, for full multi-database support)
- MongoDB 7+ (optional, for full multi-database support)

## Troubleshooting

1. **Database Connection Issues**: Check if MySQL service is running
2. **Port Conflicts**: Make sure ports 8000 and 8501 are available
3. **Import Errors**: Run `pip install -r requirements.txt` again
4. **Unicode Errors**: This Windows setup script handles encoding issues

For the complete documentation, see README.md
