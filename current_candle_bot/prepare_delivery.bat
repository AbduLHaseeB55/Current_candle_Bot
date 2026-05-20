@echo off
REM ========================================
REM FINAL DELIVERY PREPARATION SCRIPT
REM Prepares bot for client handover
REM ========================================

echo ========================================
echo CURRENT CANDLE BOT - DELIVERY PREP
echo ========================================
echo.

REM Check Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Install Python 3.10+ first.
    pause
    exit /b 1
)

echo [1/8] Checking environment...
if not exist "venv\" (
    echo [ERROR] Virtual environment not found! Run: python -m venv venv
    pause
    exit /b 1
)

echo [2/8] Activating virtual environment...
call venv\Scripts\activate

echo [3/8] Checking .env configuration...
if not exist ".env" (
    echo [ERROR] .env file missing! Copy .env.template and configure it.
    pause
    exit /b 1
)

echo [4/8] Verifying model exists...
if not exist "models\current_candle_lstm.pt" (
    echo [ERROR] Model file missing! Train model first.
    pause
    exit /b 1
)

echo [5/8] Backing up current model...
if not exist "models\backup\" mkdir models\backup
copy /Y "models\current_candle_lstm.pt" "models\backup\current_candle_lstm_%date:~-4,4%%date:~-10,2%%date:~-7,2%.pt" >nul

echo [6/8] Testing components...
python test_components.py
if %errorlevel% neq 0 (
    echo [ERROR] Component tests failed! Check logs.
    pause
    exit /b 1
)

echo [7/8] Testing Telegram connection...
python -c "from telegram_notifier import TelegramNotifier; import asyncio; from dotenv import load_dotenv; import os; load_dotenv(); bot = TelegramNotifier(os.getenv('TELEGRAM_BOT_TOKEN'), os.getenv('TELEGRAM_CHAT_ID')); asyncio.run(bot.send_message('✅ Delivery Test: Bot Ready!'))"
if %errorlevel% neq 0 (
    echo [WARNING] Telegram test failed - check credentials in .env
    echo Bot will still work, but alerts will only log locally.
)

echo [8/8] Checking dataset...
python -c "import os; print(f'Dataset size: {os.path.getsize(\"data/candles_15m.csv\")/1024/1024:.1f}MB')"

echo.
echo ========================================
echo DELIVERY PREPARATION COMPLETE
echo ========================================
echo.
echo Next steps:
echo 1. Set up 24/7 service (Task Scheduler or systemd)
echo 2. Run bot for 7 days stability test
echo 3. Review FINAL_DELIVERY_CHECKLIST.md
echo 4. Package files for client
echo.
echo To start bot now: python run_bot.py
echo.
pause
