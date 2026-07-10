@echo off
echo ========================================
echo Career OS - Restore Utility
echo ========================================
echo.

:: Check if backup name provided
if "%1"=="" (
    echo Usage: restore.bat [backup_name]
    echo.
    echo Available backups:
    if exist backups (
        dir /b backups
    ) else (
        echo No backups found
    )
    echo.
    pause
    exit /b 1
)

set BACKUP_NAME=%1
set BACKUP_DIR=backups\%BACKUP_NAME%

:: Check if backup exists
if not exist %BACKUP_DIR% (
    echo ERROR: Backup '%BACKUP_NAME%' not found!
    echo.
    echo Available backups:
    if exist backups (
        dir /b backups
    ) else (
        echo No backups found
    )
    pause
    exit /b 1
)

:: Confirm restore
echo You are about to restore from: %BACKUP_NAME%
echo.
echo ⚠️  WARNING: This will overwrite current data!
echo.
set /p CONFIRM="Type 'yes' to continue: "
if not "%CONFIRM%"=="yes" (
    echo Restore cancelled.
    pause
    exit /b 0
)

echo.
echo Starting restore...
echo.

:: Restore database
echo [1/4] Restoring database...
if exist %BACKUP_DIR%\career_os.db (
    copy /Y %BACKUP_DIR%\career_os.db services\ml-core\app\data\career_os.db > nul
    echo ✓ Database restored
) else (
    echo ℹ️  No database in backup
)

:: Restore profile
echo.
echo [2/4] Restoring profile...
if exist %BACKUP_DIR%\profile.json (
    copy /Y %BACKUP_DIR%\profile.json services\ml-core\app\data\profile.json > nul
    echo ✓ Profile restored
) else (
    echo ℹ️  No profile in backup
)

:: Restore .env
echo.
echo [3/4] Restoring configuration...
if exist %BACKUP_DIR%\.env.backup (
    copy /Y %BACKUP_DIR%\.env.backup services\ml-core\.env > nul
    echo ✓ Configuration restored
) else (
    echo ℹ️  No configuration in backup
)

:: Restore logs
echo.
echo [4/4] Restoring logs...
if exist %BACKUP_DIR%\career_os.log (
    copy /Y %BACKUP_DIR%\career_os.log services\ml-core\career_os.log > nul
    echo ✓ Logs restored
) else (
    echo ℹ️  No logs in backup
)

:: Summary
echo.
echo ========================================
echo Restore Complete!
echo ========================================
echo.
echo Data restored from: %BACKUP_NAME%
echo.
echo Next step: Restart backend if running
echo   Press Ctrl+C in backend window
echo   Run: start.bat
echo.
pause
