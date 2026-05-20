@echo off
REM ========================================
REM AUTOMATED TASK SCHEDULER SETUP
REM Creates 24/7 task automatically
REM Run as Administrator
REM ========================================

echo ========================================
echo AUTO-SETUP 24/7 TASK SCHEDULER
echo ========================================
echo.

REM Check if running as admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Please run as Administrator!
    echo Right-click this file and select "Run as administrator"
    pause
    exit /b 1
)

REM Get current directory
set BOT_DIR=%~dp0
set BOT_DIR=%BOT_DIR:~0,-1%

echo [INFO] Bot directory: %BOT_DIR%
echo.

REM Check venv exists
if not exist "%BOT_DIR%\venv\Scripts\python.exe" (
    echo [ERROR] Python virtual environment not found!
    echo Expected: %BOT_DIR%\venv\Scripts\python.exe
    pause
    exit /b 1
)

echo [1/4] Checking if task already exists...
schtasks /query /tn "TradingBot" >nul 2>&1
if %errorlevel% equ 0 (
    echo [WARNING] Task already exists. Deleting old task...
    schtasks /delete /tn "TradingBot" /f
)

echo [2/4] Creating Task Scheduler XML configuration...
set TASK_XML=%TEMP%\trading_bot_task.xml

REM Create XML file
(
echo ^<?xml version="1.0" encoding="UTF-16"?^>
echo ^<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task"^>
echo   ^<RegistrationInfo^>
echo     ^<Description^>Current Candle Trading Bot - Auto-restarts on failure^</Description^>
echo   ^</RegistrationInfo^>
echo   ^<Triggers^>
echo     ^<BootTrigger^>
echo       ^<Enabled^>true^</Enabled^>
echo     ^</BootTrigger^>
echo   ^</Triggers^>
echo   ^<Principals^>
echo     ^<Principal id="Author"^>
echo       ^<LogonType^>Password^</LogonType^>
echo       ^<RunLevel^>HighestAvailable^</RunLevel^>
echo     ^</Principal^>
echo   ^</Principals^>
echo   ^<Settings^>
echo     ^<MultipleInstancesPolicy^>IgnoreNew^</MultipleInstancesPolicy^>
echo     ^<DisallowStartIfOnBatteries^>false^</DisallowStartIfOnBatteries^>
echo     ^<StopIfGoingOnBatteries^>false^</StopIfGoingOnBatteries^>
echo     ^<AllowHardTerminate^>true^</AllowHardTerminate^>
echo     ^<StartWhenAvailable^>true^</StartWhenAvailable^>
echo     ^<RunOnlyIfNetworkAvailable^>true^</RunOnlyIfNetworkAvailable^>
echo     ^<IdleSettings^>
echo       ^<StopOnIdleEnd^>false^</StopOnIdleEnd^>
echo       ^<RestartOnIdle^>false^</RestartOnIdle^>
echo     ^</IdleSettings^>
echo     ^<AllowStartOnDemand^>true^</AllowStartOnDemand^>
echo     ^<Enabled^>true^</Enabled^>
echo     ^<Hidden^>false^</Hidden^>
echo     ^<RunOnlyIfIdle^>false^</RunOnlyIfIdle^>
echo     ^<WakeToRun^>false^</WakeToRun^>
echo     ^<ExecutionTimeLimit^>PT0S^</ExecutionTimeLimit^>
echo     ^<Priority^>7^</Priority^>
echo     ^<RestartOnFailure^>
echo       ^<Interval^>PT5M^</Interval^>
echo       ^<Count^>3^</Count^>
echo     ^</RestartOnFailure^>
echo   ^</Settings^>
echo   ^<Actions Context="Author"^>
echo     ^<Exec^>
echo       ^<Command^>%BOT_DIR%\venv\Scripts\python.exe^</Command^>
echo       ^<Arguments^>run_bot.py^</Arguments^>
echo       ^<WorkingDirectory^>%BOT_DIR%^</WorkingDirectory^>
echo     ^</Exec^>
echo   ^</Actions^>
echo ^</Task^>
) > "%TASK_XML%"

echo [3/4] Registering task with Task Scheduler...
schtasks /create /tn "TradingBot" /xml "%TASK_XML%" /ru "%USERNAME%"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create task!
    del "%TASK_XML%"
    pause
    exit /b 1
)

REM Clean up
del "%TASK_XML%"

echo [4/4] Starting task now...
schtasks /run /tn "TradingBot"

echo.
echo Waiting 5 seconds for bot to start...
timeout /t 5 /nobreak >nul

REM Check if bot is running
tasklist | findstr python.exe >nul
if %errorlevel% equ 0 (
    echo [SUCCESS] Bot is running!
) else (
    echo [WARNING] Bot may not have started. Check Task Scheduler.
)

echo.
echo ========================================
echo SETUP COMPLETE!
echo ========================================
echo.
echo Task Name: TradingBot
echo Trigger: At system startup
echo Auto-Restart: Yes (every 5 min, up to 3 times)
echo.
echo Management Commands:
echo   schtasks /run /tn "TradingBot"      # Start task
echo   schtasks /end /tn "TradingBot"      # Stop task
echo   schtasks /query /tn "TradingBot"    # Check status
echo   tasklist ^| findstr python.exe       # Check if running
echo.
echo View logs: logs\inference.log
echo.
pause
