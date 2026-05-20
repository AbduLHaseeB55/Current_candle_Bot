@echo off
REM ========================================
REM 24/7 BOT SETUP - NO ADMIN REQUIRED
REM Creates startup shortcut instead
REM ========================================

echo ========================================
echo 24/7 BOT SETUP (No Admin Required)
echo ========================================
echo.

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

echo [1/4] Creating startup batch script...
set STARTUP_SCRIPT=%BOT_DIR%\start_bot_24_7.bat

(
echo @echo off
echo cd /d "%BOT_DIR%"
echo start /B "" "%BOT_DIR%\venv\Scripts\python.exe" run_bot.py
echo exit
) > "%STARTUP_SCRIPT%"

echo [2/4] Creating startup shortcut...
set STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set SHORTCUT=%STARTUP_FOLDER%\TradingBot.lnk

REM Create VBS script to create shortcut
set VBS_SCRIPT=%TEMP%\create_shortcut.vbs
(
echo Set oWS = WScript.CreateObject("WScript.Shell"^)
echo sLinkFile = "%SHORTCUT%"
echo Set oLink = oWS.CreateShortcut(sLinkFile^)
echo oLink.TargetPath = "%STARTUP_SCRIPT%"
echo oLink.WorkingDirectory = "%BOT_DIR%"
echo oLink.Description = "Trading Bot Auto-Start"
echo oLink.Save
) > "%VBS_SCRIPT%"

cscript //nologo "%VBS_SCRIPT%"
del "%VBS_SCRIPT%"

if exist "%SHORTCUT%" (
    echo [SUCCESS] Startup shortcut created!
) else (
    echo [WARNING] Could not create shortcut
)

echo [3/4] Creating manual start script...
set MANUAL_START=%BOT_DIR%\start_bot_now.bat

(
echo @echo off
echo cd /d "%BOT_DIR%"
echo echo Starting Trading Bot...
echo start /B "" "%BOT_DIR%\venv\Scripts\python.exe" run_bot.py
echo echo Bot started in background!
echo echo.
echo echo Check if running: tasklist ^| findstr python.exe
echo echo View logs: powershell Get-Content logs\inference.log -Wait -Tail 20
echo echo.
echo pause
) > "%MANUAL_START%"

echo [4/4] Starting bot now...
start /B "" "%BOT_DIR%\venv\Scripts\python.exe" run_bot.py

echo.
echo Waiting 3 seconds...
timeout /t 3 /nobreak >nul

REM Check if bot is running
tasklist | findstr python.exe >nul
if %errorlevel% equ 0 (
    echo [SUCCESS] Bot is running!
) else (
    echo [WARNING] Bot may not have started
)

echo.
echo ========================================
echo SETUP COMPLETE!
echo ========================================
echo.
echo Bot will now:
echo  - Start automatically when you log in
echo  - Run in background (no visible window)
echo  - Continue until you stop it
echo.
echo Management:
echo  - Start: Double-click start_bot_now.bat
echo  - Stop:  taskkill /F /IM python.exe
echo  - Check: tasklist ^| findstr python.exe
echo  - Logs:  powershell Get-Content logs\inference.log -Wait -Tail 20
echo.
echo Startup shortcut: %STARTUP_FOLDER%\TradingBot.lnk
echo.
pause
