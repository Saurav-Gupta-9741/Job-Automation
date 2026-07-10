@echo off
echo ========================================
echo Career OS - System Diagnostics
echo ========================================
echo.
echo Running comprehensive system checks...
echo.

:: Variables for tracking issues
set ISSUES=0

:: Check 1: Python
echo [1/15] Python Installation
python --version 2>&1 | find "Python 3" > nul
if %errorlevel% neq 0 (
    echo ❌ Python 3 not found or not in PATH
    set /a ISSUES+=1
) else (
    python --version
    echo ✓ Python OK
)
echo.

:: Check 2: Virtual Environment
echo [2/15] Virtual Environment
if exist services\ml-core\.venv (
    echo ✓ Virtual environment exists
) else (
    echo ❌ Virtual environment missing - run setup.bat
    set /a ISSUES+=1
)
echo.

:: Check 3: .env file
echo [3/15] Environment Configuration
if exist services\ml-core\.env (
    echo ✓ .env file exists
    findstr /C:"GROQ_API_KEY=gsk_" services\ml-core\.env > nul
    if %errorlevel% neq 0 (
        echo ⚠️  GROQ_API_KEY may not be set correctly
        set /a ISSUES+=1
    ) else (
        echo ✓ GROQ_API_KEY appears to be set
    )
) else (
    echo ❌ .env file missing - run setup.bat
    set /a ISSUES+=1
)
echo.

:: Check 4: Profile
echo [4/15] Profile Configuration
if exist services\ml-core\app\data\profile.json (
    echo ✓ profile.json exists
    findstr /C:"john.doe@example.com" services\ml-core\app\data\profile.json > nul
    if %errorlevel% equ 0 (
        echo ⚠️  Still using default profile - update with your info
    ) else (
        echo ✓ Profile appears customized
    )
) else (
    echo ❌ profile.json missing
    set /a ISSUES+=1
)
echo.

:: Check 5: Database
echo [5/15] Database
if exist services\ml-core\app\data\career_os.db (
    echo ✓ Database file exists
    for %%A in (services\ml-core\app\data\career_os.db) do set DBSIZE=%%~zA
    echo   Size: %DBSIZE% bytes
) else (
    echo ⚠️  Database not created yet (will be created on first run)
)
echo.

:: Check 6: Backend Port
echo [6/15] Backend Port (8000)
netstat -ano | findstr ":8000" | findstr "LISTENING" > nul
if %errorlevel% equ 0 (
    echo ✓ Backend is running on port 8000
) else (
    echo ℹ️  Backend not running (start with start.bat)
)
echo.

:: Check 7: Backend Health (if running)
echo [7/15] Backend Health Check
curl -s --connect-timeout 2 http://127.0.0.1:8000/health > nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Backend responding
    curl -s http://127.0.0.1:8000/health | findstr "ok"
) else (
    echo ℹ️  Backend not responding (start with start.bat)
)
echo.

:: Check 8: Dependencies
echo [8/15] Python Dependencies
if exist services\ml-core\.venv\Scripts\python.exe (
    cd services\ml-core
    call .venv\Scripts\activate.bat
    python -c "import fastapi, anthropic, sqlite3" 2>nul
    if %errorlevel% neq 0 (
        echo ❌ Required Python packages missing - run setup.bat
        set /a ISSUES+=1
    ) else (
        echo ✓ Core dependencies installed
    )
    cd ..\..
) else (
    echo ⚠️  Cannot check - virtual environment missing
)
echo.

:: Check 9: Extension Files
echo [9/15] Extension Files
if exist apps\extension\manifest.json (
    echo ✓ Extension manifest exists
) else (
    echo ❌ Extension manifest missing
    set /a ISSUES+=1
)
if exist apps\extension\background.js (
    echo ✓ Extension background script exists
) else (
    echo ❌ Extension background script missing
    set /a ISSUES+=1
)
if exist apps\extension\content\agent.js (
    echo ✓ Extension content scripts exist
) else (
    echo ❌ Extension content scripts missing
    set /a ISSUES+=1
)
echo.

:: Check 10: Log Files
echo [10/15] Log Files
if exist services\ml-core\career_os.log (
    for %%A in (services\ml-core\career_os.log) do set LOGSIZE=%%~zA
    echo ✓ Backend log exists (Size: %LOGSIZE% bytes)
    echo   Last 3 errors:
    findstr /C:"ERROR" services\ml-core\career_os.log | more +0 > nul 2>&1
    if %errorlevel% equ 0 (
        powershell -command "Get-Content services\ml-core\career_os.log | Select-String 'ERROR' | Select-Object -Last 3"
    ) else (
        echo   No errors logged
    )
) else (
    echo ℹ️  No log file yet (created on first backend run)
)
echo.

:: Check 11: Disk Space
echo [11/15] Disk Space
for /f "tokens=3" %%a in ('dir /-c ^| findstr "bytes free"') do set FREESPACE=%%a
echo ✓ Free disk space: %FREESPACE% bytes
echo.

:: Check 12: Internet Connectivity
echo [12/15] Internet Connectivity
ping -n 1 console.groq.com > nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Can reach Groq API
) else (
    echo ❌ Cannot reach Groq API - check internet connection
    set /a ISSUES+=1
)
echo.

:: Check 13: Required Directories
echo [13/15] Directory Structure
set MISSING_DIRS=0
if not exist services\ml-core\app (echo ❌ Missing: services\ml-core\app & set /a MISSING_DIRS+=1)
if not exist services\ml-core\app\adapters (echo ❌ Missing: services\ml-core\app\adapters & set /a MISSING_DIRS+=1)
if not exist services\ml-core\app\llm (echo ❌ Missing: services\ml-core\app\llm & set /a MISSING_DIRS+=1)
if not exist apps\extension\content (echo ❌ Missing: apps\extension\content & set /a MISSING_DIRS+=1)
if %MISSING_DIRS% equ 0 (
    echo ✓ All required directories present
) else (
    echo Found %MISSING_DIRS% missing directories
    set /a ISSUES+=1
)
echo.

:: Check 14: Git Status (if git available)
echo [14/15] Version Control
git --version > nul 2>&1
if %errorlevel% equ 0 (
    git status > nul 2>&1
    if %errorlevel% equ 0 (
        echo ✓ Git repository detected
        for /f %%i in ('git status --porcelain 2^>nul ^| find /c /v ""') do set CHANGES=%%i
        echo   Uncommitted changes: %CHANGES%
    ) else (
        echo ℹ️  Not a git repository
    )
) else (
    echo ℹ️  Git not installed
)
echo.

:: Check 15: Stats Summary (if backend running)
echo [15/15] Application Statistics
curl -s --connect-timeout 2 http://127.0.0.1:8000/api/stats?days=7 2>nul | findstr "total_sessions" > nul
if %errorlevel% equ 0 (
    echo ✓ Statistics available
    curl -s http://127.0.0.1:8000/api/stats?days=7 | findstr /C:"total_sessions" /C:"completed_sessions" /C:"completion_rate"
) else (
    echo ℹ️  No statistics yet (apply to some jobs first!)
)
echo.

:: Summary
echo ========================================
echo Diagnostic Summary
echo ========================================
echo.
if %ISSUES% equ 0 (
    echo ✅ System Status: HEALTHY
    echo No critical issues detected!
    echo.
    echo Ready to test? Try:
    echo   1. start.bat    - Start backend
    echo   2. test.bat     - Run system tests
    echo   3. Open Chrome and load extension
) else (
    echo ⚠️  System Status: NEEDS ATTENTION
    echo Found %ISSUES% issue(s) that need fixing
    echo.
    echo Fix issues by:
    echo   1. Run setup.bat if not done yet
    echo   2. Check .env has valid GROQ_API_KEY
    echo   3. Update profile.json with your info
    echo   4. Ensure all files are present
)
echo.
echo ========================================

pause
