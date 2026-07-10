@echo off
echo ========================================
echo Career OS - Export Report
echo ========================================
echo.

:: Check if backend is running
curl -s --connect-timeout 2 http://127.0.0.1:8000/health > nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Backend not running!
    echo    Start backend first: start.bat
    pause
    exit /b 1
)

:: Create reports directory
if not exist reports (
    mkdir reports
    echo Created reports directory
)

:: Generate timestamp
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set TIMESTAMP=%datetime:~0,8%_%datetime:~8,6%

:: Report filename
set REPORT_FILE=reports\career_os_report_%TIMESTAMP%.txt

echo Generating comprehensive report...
echo.

:: Generate report
(
    echo ========================================
    echo Career OS - Application Report
    echo ========================================
    echo Generated: %date% %time%
    echo.
    
    echo [SYSTEM HEALTH]
    curl -s http://127.0.0.1:8000/health
    echo.
    echo.
    
    echo [7-DAY STATISTICS]
    curl -s http://127.0.0.1:8000/api/stats?days=7
    echo.
    echo.
    
    echo [30-DAY STATISTICS]
    curl -s http://127.0.0.1:8000/api/stats?days=30
    echo.
    echo.
    
    echo [ALL-TIME STATISTICS]
    curl -s http://127.0.0.1:8000/api/stats?days=9999
    echo.
    echo.
    
    echo [ALL APPLICATIONS]
    curl -s http://127.0.0.1:8000/api/applications
    echo.
    echo.
    
    echo [DATABASE DETAILS]
    cd services\ml-core
    call .venv\Scripts\activate.bat
    python -c "import sqlite3; conn = sqlite3.connect('app/data/career_os.db'); cur = conn.cursor(); print(f'Total Applications: {cur.execute(\"SELECT COUNT(*) FROM applications\").fetchone()[0]}'); print(f'Submitted: {cur.execute(\"SELECT COUNT(*) FROM applications WHERE submitted=1\").fetchone()[0]}'); print(f'In Progress: {cur.execute(\"SELECT COUNT(*) FROM applications WHERE submitted=0\").fetchone()[0]}'); print(f'Field Memory Entries: {cur.execute(\"SELECT COUNT(*) FROM field_memory\").fetchone()[0]}'); print(f'Unique Questions Learned: {cur.execute(\"SELECT COUNT(DISTINCT q_raw) FROM field_memory\").fetchone()[0]}'); conn.close()"
    cd ..\..
    echo.
    echo.
    
    echo ========================================
    echo End of Report
    echo ========================================
) > %REPORT_FILE%

echo ✓ Report generated successfully!
echo.
echo Report location: %REPORT_FILE%

:: Show file size
for %%A in (%REPORT_FILE%) do set REPORT_SIZE=%%~zA
echo Report size: %REPORT_SIZE% bytes
echo.

:: Also export CSV
echo Exporting CSV data...
curl -s http://127.0.0.1:8000/api/export/csv > reports\applications_%TIMESTAMP%.csv 2>nul
if %errorlevel% equ 0 (
    echo ✓ CSV exported: reports\applications_%TIMESTAMP%.csv
) else (
    echo ℹ️  CSV export not available (check backend logs)
)

echo.
echo ========================================

:: Ask if user wants to view the report
set /p VIEW="View report now? (y/n): "
if /i "%VIEW%"=="y" (
    type %REPORT_FILE% | more
)

pause
