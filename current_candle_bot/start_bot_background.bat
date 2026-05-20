@echo off
REM Current Candle Bot - Background Service Starter
REM Uses pythonw.exe to run in background without console window

echo Starting Current Candle Bot in background...

cd /d "%~dp0"

REM Activate virtual environment and start bot in background
start /B venv\Scripts\pythonw.exe run_bot.py

echo Bot started in background!
echo Check logs\inference.log for status

timeout /t 3
