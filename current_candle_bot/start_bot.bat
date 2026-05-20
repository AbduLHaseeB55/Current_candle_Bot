@echo off
REM Current Candle Bot - Windows Service Runner
REM This script starts the bot as a background process

echo ============================================
echo  Current Candle Bot - Starting Service
echo ============================================

cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run setup_env.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if .env exists
if not exist ".env" (
    echo ERROR: .env file not found!
    echo Please copy .env.template to .env and configure it
    pause
    exit /b 1
)

REM Check if model exists
if not exist "models\current_candle_lstm.pt" (
    echo WARNING: Model file not found!
    echo Please train the model using the notebook first
    echo Or create a dummy model for testing
)

REM Start the bot
echo Starting bot...
python run_bot.py

pause
