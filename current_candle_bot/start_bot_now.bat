@echo off
cd /d "E:\Haseeb\current_candle_bot\current_candle_bot"
echo Starting Trading Bot...
start /B "" "E:\Haseeb\current_candle_bot\current_candle_bot\venv\Scripts\python.exe" run_bot.py
echo Bot started in background!
echo.
echo Check if running: tasklist | findstr python.exe
echo View logs: powershell Get-Content logs\inference.log -Wait -Tail 20
echo.
pause
