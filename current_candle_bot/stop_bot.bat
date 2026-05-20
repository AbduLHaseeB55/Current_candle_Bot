@echo off
REM Stop the Current Candle Bot

echo Stopping Current Candle Bot...

REM Kill Python process running run_bot.py
taskkill /FI "WINDOWTITLE eq run_bot.py*" /F 2>nul
taskkill /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *run_bot*" /F 2>nul
taskkill /FI "IMAGENAME eq pythonw.exe" /FI "WINDOWTITLE eq *run_bot*" /F 2>nul

echo Bot stopped!
pause
