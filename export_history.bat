@echo off
echo ===========================================
echo       Git History Logbook Generator
echo ===========================================
echo.

REM Check if config file exists
if not exist "config.json" (
    echo Error: config.json not found!
    echo Please make sure the configuration file exists.
    echo.
    pause
    exit /b 1
)

echo Exporting commit history from all repositories...
echo Including project information and author filtering...
echo.

REM Generate logbook with timestamp
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "timestamp=%YYYY%-%MM%-%DD%_%HH%-%Min%"

python git_history_logbook.py --config config.json --output "commit_logbook_%timestamp%" --csv "commits_%timestamp%.csv"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ===========================================
    echo    Export completed successfully!
    echo ===========================================
    echo.
    echo Generated files:
    dir /b commit_logbook_%timestamp%.*
    dir /b commits_%timestamp%.csv
    echo.
    echo Open the HTML file in your browser to view the logbook.
) else (
    echo.
    echo ===========================================
    echo         Export failed!
    echo ===========================================
    echo.
)

pause 