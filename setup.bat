@echo off
echo ========================================
echo Career OS - Automated Setup Script
echo ========================================
echo.

:: Check Python
echo [1/6] Checking Python installation...
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)
echo ✓ Python found

:: Navigate to backend
echo.
echo [2/6] Setting up backend...
cd services\ml-core

:: Create virtual environment
echo Creating virtual environment...
if exist .venv (
    echo Virtual environment already exists
) else (
    python -m venv .venv
    echo ✓ Virtual environment created
)

:: Activate and install
echo.
echo [3/6] Installing dependencies...
call .venv\Scripts\activate.bat
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo ✓ Dependencies installed

:: Setup config
echo.
echo [4/6] Setting up configuration...
if exist .env (
    echo ✓ .env file already exists
) else (
    copy .env.example .env > nul
    echo ✓ Created .env from template
    echo.
    echo ⚠️  IMPORTANT: Edit .env and add your GROQ_API_KEY
    echo    Get your key from: https://console.groq.com/keys
    echo.
)

:: Setup profile
echo.
echo [5/6] Setting up profile...
if exist app\data\profile.json (
    echo ✓ profile.json already exists
) else (
    echo Creating default profile.json...
    mkdir app\data 2>nul
    echo { > app\data\profile.json
    echo   "first_name": "John", >> app\data\profile.json
    echo   "last_name": "Doe", >> app\data\profile.json
    echo   "email": "john.doe@example.com", >> app\data\profile.json
    echo   "phone": "+1-555-0123", >> app\data\profile.json
    echo   "location": "San Francisco, CA", >> app\data\profile.json
    echo   "years_experience": "5" >> app\data\profile.json
    echo } >> app\data\profile.json
    echo ✓ Created default profile
    echo.
    echo ⚠️  IMPORTANT: Edit app\data\profile.json with your real information
    echo.
)

:: Run tests
echo.
echo [6/6] Running automated tests...
pytest tests\test_robustness.py -v --tb=short
if %errorlevel% neq 0 (
    echo.
    echo ⚠️  Some tests failed - review output above
) else (
    echo ✓ All tests passed!
)

:: Summary
echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env and add your GROQ_API_KEY
echo 2. Edit app\data\profile.json with your information
echo 3. Run: start.bat
echo.
echo Or manually start backend:
echo   cd services\ml-core
echo   .venv\Scripts\activate
echo   python -m app.main
echo.
pause
