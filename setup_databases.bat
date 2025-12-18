@echo off
REM Multi-Tenant NLP2SQL Database Setup Script for Windows

echo [SETUP] Setting up Multi-Tenant NLP2SQL Database System...
echo.

REM Create exports directory
if not exist "exports" mkdir exports

echo [DATA] Setting up MySQL metadata database...
mysql -u root -ppassword -e "DROP DATABASE IF EXISTS nlp2sql_metadata;"
mysql -u root -ppassword -e "CREATE DATABASE nlp2sql_metadata;"
mysql -u root -ppassword nlp2sql_metadata < database\schema.sql
mysql -u root -ppassword nlp2sql_metadata < database\complete_sample_data.sql

echo.
echo [OK] Database setup completed!
echo.
echo [DATA] Database Summary:
echo - MySQL metadata: nlp2sql_metadata (Central system)
echo - Organization databases will be created when first accessed
echo.
echo [USERS] Sample users created (250 total across 5 organizations)
echo [AUTH] All passwords: password123
echo.
echo [INFO] For full multi-database setup, install PostgreSQL and MongoDB
echo [INFO] Then run the organization-specific setup scripts
pause
