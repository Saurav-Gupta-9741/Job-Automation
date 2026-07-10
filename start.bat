@echo off
echo ========================================
echo Career OS - Starting Backend
echo ========================================
echo.

:: Check if setup was run
if not exist services\ml-core\.venv (
    echo ERROR: Virtual environment not found!
    echo Please run setup.bat first
    pause
    exit /b 1
)

:: Check if .env exists
if not exist services\ml-core\.env (
    echo ERROR: .env file not found!
    echo Please run setup.bat first
    pause
    exit /b 1
)

:: Start backend
cd services\ml-core
call .venv\Scripts\activate.bat

echo Starting Career OS backend...
echo.
echo ℹ️  Backend will run at: http://127.0.0.1:8000
echo ℹ️  Health check: http://127.0.0.1:8000/health
echo ℹ️  Stats: http://127.0.0.1:8000/api/stats
echo.
echo Press Ctrl+C to stop
echo ========================================
echo.

python -m app.main
