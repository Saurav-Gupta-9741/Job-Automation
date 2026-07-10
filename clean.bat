@echo off
echo ========================================
echo Career OS - Cleanup Utility
echo ========================================
echo.
echo This will clean temporary files and caches
echo.

set /p CONFIRM="Continue with cleanup? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo Cancelled.
    pause
    exit /b 0
)

echo.
echo Starting cleanup...
echo.

:: Clean Python cache
echo [1/6] Cleaning Python cache files...
set PYCACHE_COUNT=0
for /r services\ml-core %%d in (__pycache__) do (
    if exist "%%d" (
        rmdir /s /q "%%d" 2>nul
        set /a PYCACHE_COUNT+=1
    )
)
for /r services\ml-core %%f in (*.pyc *.pyo) do (
    if exist "%%f" (
        del /q "%%f" 2>nul
        set /a PYCACHE_COUNT+=1
    )
)
echo ✓ Removed %PYCACHE_COUNT% Python cache items
echo.

:: Clean log files (optional)
echo [2/6] Cleaning old log files...
set /p CLEAN_LOGS="Remove backend log file? This will delete error history (y/n): "
if /i "%CLEAN_LOGS%"=="y" (
    if exist services\ml-core\career_os.log (
        del /q services\ml-core\career_os.log
        echo ✓ Removed log file
    ) else (
        echo ℹ️  No log file found
    )
) else (
    echo ⊘ Kept log file
)
echo.

:: Clean old backups
echo [3/6] Cleaning old backups...
if exist backups (
    for /f %%i in ('dir /b backups\career_os_backup_*.db 2^>nul ^| find /c ".db"') do set BACKUP_COUNT=%%i
    if %BACKUP_COUNT% gtr 10 (
        echo Found %BACKUP_COUNT% backups
        set /p CLEAN_BACKUPS="Keep only 10 most recent backups? (y/n): "
        if /i "!CLEAN_BACKUPS!"=="y" (
            :: Delete oldest backups, keep 10
            for /f "skip=10 tokens=*" %%f in ('dir /b /o-d backups\career_os_backup_*.db 2^>nul') do (
                del /q "backups\%%f"
                echo   Removed %%f
            )
            echo ✓ Cleaned old backups
        ) else (
            echo ⊘ Kept all backups
        )
    ) else (
        echo ✓ Only %BACKUP_COUNT% backups (no cleanup needed)
    )
) else (
    echo ℹ️  No backups directory
)
echo.

:: Clean old reports
echo [4/6] Cleaning old reports...
if exist reports (
    for /f %%i in ('dir /b reports\career_os_report_*.txt 2^>nul ^| find /c ".txt"') do set REPORT_COUNT=%%i
    if %REPORT_COUNT% gtr 10 (
        echo Found %REPORT_COUNT% reports
        set /p CLEAN_REPORTS="Keep only 10 most recent reports? (y/n): "
        if /i "!CLEAN_REPORTS!"=="y" (
            for /f "skip=10 tokens=*" %%f in ('dir /b /o-d reports\career_os_report_*.txt 2^>nul') do (
                del /q "reports\%%f"
            )
            for /f "skip=10 tokens=*" %%f in ('dir /b /o-d reports\applications_*.csv 2^>nul') do (
                del /q "reports\%%f"
            )
            echo ✓ Cleaned old reports
        ) else (
            echo ⊘ Kept all reports
        )
    ) else (
        echo ✓ Only %REPORT_COUNT% reports (no cleanup needed)
    )
) else (
    echo ℹ️  No reports directory
)
echo.

:: Optimize database (vacuum)
echo [5/6] Optimizing database...
if exist services\ml-core\app\data\career_os.db (
    for %%A in (services\ml-core\app\data\career_os.db) do set BEFORE_SIZE=%%~zA
    echo Before: %BEFORE_SIZE% bytes
    
    cd services\ml-core
    call .venv\Scripts\activate.bat
    python -c "import sqlite3; conn = sqlite3.connect('app/data/career_os.db'); conn.execute('VACUUM'); conn.close()" 2>nul
    cd ..\..
    
    for %%A in (services\ml-core\app\data\career_os.db) do set AFTER_SIZE=%%~zA
    echo After: %AFTER_SIZE% bytes
    set /a SAVED=%BEFORE_SIZE%-%AFTER_SIZE%
    echo ✓ Saved %SAVED% bytes
) else (
    echo ℹ️  No database yet
)
echo.

:: Temporary files
echo [6/6] Cleaning temporary files...
set TEMP_COUNT=0
if exist *.tmp (
    del /q *.tmp 2>nul
    set /a TEMP_COUNT+=1
)
if exist services\ml-core\*.tmp (
    del /q services\ml-core\*.tmp 2>nul
    set /a TEMP_COUNT+=1
)
echo ✓ Removed %TEMP_COUNT% temporary files
echo.

echo ========================================
echo Cleanup Complete!
echo ========================================
echo.
echo Space optimization and cache cleanup finished.
echo Your Career OS installation is now cleaner.
echo.

pause
