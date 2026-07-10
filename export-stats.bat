@echo off
echo ========================================
echo Career OS - Export Statistics
echo ========================================
echo.

:: Create exports directory
if not exist exports mkdir exports

:: Generate filename with timestamp
set TIMESTAMP=%date:~-4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%

:: Check backend
curl -s --connect-timeout 2 http://127.0.0.1:8000/health >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Backend not running!
    echo Please start backend first: start.bat
    pause
    exit /b 1
)

echo Exporting data from Career OS...
echo.

:: Export CSV
echo [1/5] Exporting applications to CSV...
curl -s http://127.0.0.1:8000/api/applications/export/csv > exports\applications_%TIMESTAMP%.csv
if %errorlevel% equ 0 (
    echo ✓ Saved to: exports\applications_%TIMESTAMP%.csv
) else (
    echo ❌ CSV export failed
)

:: Export All Applications JSON
echo.
echo [2/5] Exporting all applications (JSON)...
curl -s http://127.0.0.1:8000/api/applications > exports\applications_%TIMESTAMP%.json
if %errorlevel% equ 0 (
    echo ✓ Saved to: exports\applications_%TIMESTAMP%.json
) else (
    echo ❌ Applications export failed
)

:: Export 7-Day Stats
echo.
echo [3/5] Exporting 7-day statistics...
curl -s "http://127.0.0.1:8000/api/stats?days=7" > exports\stats_7days_%TIMESTAMP%.json
if %errorlevel% equ 0 (
    echo ✓ Saved to: exports\stats_7days_%TIMESTAMP%.json
) else (
    echo ❌ Stats export failed
)

:: Export 30-Day Stats
echo.
echo [4/5] Exporting 30-day statistics...
curl -s "http://127.0.0.1:8000/api/stats?days=30" > exports\stats_30days_%TIMESTAMP%.json
if %errorlevel% equ 0 (
    echo ✓ Saved to: exports\stats_30days_%TIMESTAMP%.json
) else (
    echo ❌ Stats export failed
)

:: Export Field Memory (learned answers)
echo.
echo [5/5] Exporting learned field answers...
curl -s http://127.0.0.1:8000/api/memory > exports\memory_%TIMESTAMP%.json
if %errorlevel% equ 0 (
    echo ✓ Saved to: exports\memory_%TIMESTAMP%.json
) else (
    echo ℹ️  Memory endpoint not available (optional)
)

:: Create summary report
echo.
echo Creating summary report...
(
    echo Career OS Export Summary
    echo ========================
    echo Export Date: %date% %time%
    echo.
    echo Files Created:
    echo - applications_%TIMESTAMP%.csv
    echo - applications_%TIMESTAMP%.json
    echo - stats_7days_%TIMESTAMP%.json
    echo - stats_30days_%TIMESTAMP%.json
    echo - memory_%TIMESTAMP%.json
    echo.
    echo Statistics:
    curl -s "http://127.0.0.1:8000/api/stats?days=30"
) > exports\EXPORT_SUMMARY_%TIMESTAMP%.txt

echo ✓ Summary created

:: Display results
echo.
echo ========================================
echo Export Complete!
echo ========================================
echo.
echo Files saved to: exports\
echo.
dir /b exports\*%TIMESTAMP%*
echo.
echo You can now:
echo - Open CSV in Excel/Google Sheets
echo - Analyze JSON with any tool
echo - Share reports with stakeholders
echo.
pause
