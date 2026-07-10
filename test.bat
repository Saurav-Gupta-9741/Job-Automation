@echo off
echo ========================================
echo Career OS - System Test
echo ========================================
echo.

:: Test 1: Backend Health
echo [Test 1/5] Checking backend health...
curl -s http://127.0.0.1:8000/health > nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Backend not responding
    echo    Make sure backend is running: start.bat
    goto :end
) else (
    echo ✓ Backend is running
)

:: Test 2: Health Check Details
echo.
echo [Test 2/5] Checking backend details...
curl -s http://127.0.0.1:8000/health
echo.

:: Test 3: Database
echo.
echo [Test 3/5] Checking database...
if exist services\ml-core\app\data\career_os.db (
    echo ✓ Database exists
) else (
    echo ❌ Database not found
    goto :end
)

:: Test 4: Stats Endpoint
echo.
echo [Test 4/5] Checking stats endpoint...
curl -s http://127.0.0.1:8000/api/stats?days=1 > nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Stats endpoint failed
    goto :end
) else (
    echo ✓ Stats endpoint working
)

:: Test 5: Applications
echo.
echo [Test 5/5] Checking applications...
for /f %%i in ('curl -s http://127.0.0.1:8000/api/applications ^| find /c "session_id"') do set COUNT=%%i
echo ✓ Found %COUNT% applications in database

:: Summary
echo.
echo ========================================
echo All Tests Passed! ✓
echo ========================================
echo.
echo System is ready for LinkedIn testing
echo.
echo Next: Open Chrome and test on LinkedIn
echo   1. Go to chrome://extensions
echo   2. Load extension from apps/extension/
echo   3. Visit linkedin.com/jobs
echo   4. Click "Apply on this page"
echo.

:end
pause
