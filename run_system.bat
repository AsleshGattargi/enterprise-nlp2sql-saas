@echo off
echo [SETUP] Multi-Tenant NLP2SQL System
echo ===============================================
echo.

REM Check if .env exists
if not exist ".env" (
    echo [ERROR] .env file not found. Please run setup_windows.py first.
    pause
    exit /b 1
)

REM Create exports directory
if not exist "exports" mkdir exports

echo [INFO] Starting system components...
echo [INFO] Backend will start on http://localhost:8000
echo [INFO] Frontend will start on http://localhost:8501
echo.
echo [INFO] Close this window to stop the system
echo.

REM Start both backend and frontend
start "FastAPI Backend" cmd /k "python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 /nobreak > nul
start "Streamlit Frontend" cmd /k "python -m streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0"

echo [OK] System started! Check the opened windows.
echo [INFO] Access the application at http://localhost:8501
pause
