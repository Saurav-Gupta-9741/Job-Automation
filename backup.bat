@echo off
echo ========================================
echo Career OS - Backup Utility
echo ========================================
echo.

:: Create backup directory
set BACKUP_DIR=backups
set TIMESTAMP=%date:~-4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set BACKUP_NAME=backup_%TIMESTAMP%

echo Creating backup: %BACKUP_NAME%
echo.

if not exist %BACKUP_DIR% mkdir %BACKUP_DIR%
if not exist %BACKUP_DIR%\%BACKUP_NAME% mkdir %BACKUP_DIR%\%BACKUP_NAME%

:: Backup database
echo [1/4] Backing up database...
if exist services\ml-core\app\data\career_os.db (
    copy services\ml-core\app\data\career_os.db %BACKUP_DIR%\%BACKUP_NAME%\career_os.db > nul
    echo ✓ Database backed up
) else (
    echo ⚠️  No database found to backup
)

:: Backup profile
echo.
echo [2/4] Backing up profile...
if exist services\ml-core\app\data\profile.json (
    copy services\ml-core\app\data\profile.json %BACKUP_DIR%\%BACKUP_NAME%\profile.json > nul
    echo ✓ Profile backed up
) else (
    echo ⚠️  No profile found to backup
)

:: Backup .env (without exposing secrets)
echo.
echo [3/4] Backing up configuration...
if exist services\ml-core\.env (
    copy services\ml-core\.env %BACKUP_DIR%\%BACKUP_NAME%\.env.backup > nul
    echo ✓ Configuration backed up
    echo ⚠️  Note: .env contains sensitive data - keep backup secure!
) else (
    echo ⚠️  No .env found to backup
)

:: Backup logs
echo.
echo [4/4] Backing up logs...
if exist services\ml-core\career_os.log (
    copy services\ml-core\career_os.log %BACKUP_DIR%\%BACKUP_NAME%\career_os.log > nul
    echo ✓ Logs backed up
) else (
    echo ℹ️  No logs found to backup
)

:: Create backup info file
echo.
echo Creating backup manifest...
(
    echo Career OS Backup
    echo ================
    echo Date: %date% %time%
    echo Backup Name: %BACKUP_NAME%
    echo.
    echo Contents:
    if exist %BACKUP_DIR%\%BACKUP_NAME%\career_os.db echo - career_os.db ^(database^)
    if exist %BACKUP_DIR%\%BACKUP_NAME%\profile.json echo - profile.json ^(user profile^)
    if exist %BACKUP_DIR%\%BACKUP_NAME%\.env.backup echo - .env.backup ^(configuration^)
    if exist %BACKUP_DIR%\%BACKUP_NAME%\career_os.log echo - career_os.log ^(logs^)
    echo.
    echo To restore:
    echo 1. Copy files back to their original locations
    echo 2. Restart the backend
) > %BACKUP_DIR%\%BACKUP_NAME%\README.txt

echo ✓ Backup manifest created

:: Summary
echo.
echo ========================================
echo Backup Complete!
echo ========================================
echo.
echo Location: %BACKUP_DIR%\%BACKUP_NAME%
echo.
dir /b %BACKUP_DIR%\%BACKUP_NAME%
echo.
echo To restore from this backup:
echo   restore.bat %BACKUP_NAME%
echo.
pause
