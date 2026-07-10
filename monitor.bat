@echo off
title Career OS - Live Monitor
echo ========================================
echo Career OS - Live Monitoring Dashboard
echo ========================================
echo.
echo Refreshing every 10 seconds...
echo Press Ctrl+C to stop
echo.

:loop
cls
echo ========================================
echo Career OS - Live Monitor
echo Updated: %date% %time%
echo ========================================
echo.

:: Backend Status
echo [BACKEND STATUS]
curl -s --connect-timeout 2 http://127.0.0.1:8000/health 2>nul | findstr "ok" >nul
if %errorlevel% equ 0 (
    echo Status: 🟢 RUNNING
    curl -s http://127.0.0.1:8000/health
) else (
    echo Status: 🔴 NOT RUNNING
    echo Start with: start.bat
)
echo.

:: Today's Stats
echo [TODAY'S STATISTICS]
curl -s --connect-timeout 2 http://127.0.0.1:8000/api/stats?days=1 2>nul > temp_stats.json
if %errorlevel% equ 0 (
    type temp_stats.json | findstr /C:"total_sessions" /C:"completed_sessions" /C:"completion_rate" /C:"avg_handoffs" /C:"memory_hit_rate"
    del temp_stats.json 2>nul
) else (
    echo No data available (backend not running)
)
echo.

:: Recent Applications
echo [RECENT APPLICATIONS - Last 5]
curl -s --connect-timeout 2 http://127.0.0.1:8000/api/applications 2>nul > temp_apps.json
if %errorlevel% equ 0 (
    powershell -command "Get-Content temp_apps.json | ConvertFrom-Json | Select-Object -First 5 | ForEach-Object { Write-Host \"- $($_.title) at $($_.company) [$($_.status)]\" }"
    del temp_apps.json 2>nul
) else (
    echo No applications yet
)
echo.

:: Database Size
echo [DATABASE]
if exist services\ml-core\app\data\career_os.db (
    for %%A in (services\ml-core\app\data\career_os.db) do (
        set DBSIZE=%%~zA
        set /a DBSIZE_KB=%%~zA/1024
    )
    echo Size: %DBSIZE_KB% KB
) else (
    echo Database not created yet
)
echo.

:: Log Status
echo [RECENT ERRORS]
if exist services\ml-core\career_os.log (
    findstr /C:"ERROR" services\ml-core\career_os.log >nul 2>&1
    if %errorlevel% equ 0 (
        powershell -command "Get-Content services\ml-core\career_os.log | Select-String 'ERROR' | Select-Object -Last 3"
    ) else (
        echo No errors in log
    )
) else (
    echo No log file yet
)
echo.

echo ========================================
echo Refreshing in 10 seconds...
echo Press Ctrl+C to stop monitoring
echo ========================================

timeout /t 10 /nobreak >nul
goto loop
