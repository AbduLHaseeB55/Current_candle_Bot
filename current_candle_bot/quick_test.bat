@echo off
REM Quick Test - Verify Bot Can Start
REM This is a 5-minute test run to catch errors before production

echo ========================================
echo Current Candle Bot - Quick Test
echo ========================================
echo.
echo This will run the bot for 5 minutes to verify:
echo   - Components load correctly
echo   - WebSocket connects to Binance
echo   - Model loads and makes predictions
echo   - Telegram connection works
echo.
echo Press Ctrl+C to stop early if you see issues.
echo.
pause

cd /d "%~dp0"

REM Activate virtual environment
call venv\Scripts\activate.bat

echo.
echo [Starting bot in test mode...]
echo.

REM Set a timeout and run the bot
timeout /t 300 /nobreak | python run_bot.py

echo.
echo ========================================
echo Test complete!
echo ========================================
echo.
echo Next: Check logs\inference.log for any errors
echo       Check if you received Telegram test message
echo.

pause
