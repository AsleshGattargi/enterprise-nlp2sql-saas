@echo off
echo ================================================================
echo      MULTI-TENANT NLP2SQL SYSTEM LAUNCHER (Windows)
echo ================================================================
echo.

echo Choose your startup mode:
echo [1] Docker Mode (Full multi-database system)
echo [2] Local Mode (Development with SQLite fallback)  
echo [3] Health Check (Test database connections)
echo [4] Test Setup (Verify installation)
echo.

set /p choice=Enter your choice (1-4): 

if "%choice%"=="1" (
    echo.
    echo Starting Docker Mode...
    python start_multi_db_system.py docker
) else if "%choice%"=="2" (
    echo.
    echo Starting Local Mode...
    python start_multi_db_system.py local
) else if "%choice%"=="3" (
    echo.
    echo Running Health Check...
    python start_multi_db_system.py check
) else if "%choice%"=="4" (
    echo.
    echo Testing Setup...
    python test_multi_db_setup.py
) else (
    echo.
    echo Invalid choice. Please run the script again and choose 1-4.
)

echo.
echo Press any key to exit...
pause >nul