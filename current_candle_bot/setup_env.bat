@echo off
echo Creating virtual environment for Current Candle Bot...

REM Create virtual environment
python -m venv venv

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip

REM Install requirements
pip install -r requirements.txt

echo.
echo Virtual environment setup complete!
echo To activate: venv\Scripts\activate.bat
echo.
echo Next steps:
echo 1. Copy .env.template to .env
echo 2. Fill in your Telegram credentials in .env
echo 3. Run: python run_bot.py
pause
