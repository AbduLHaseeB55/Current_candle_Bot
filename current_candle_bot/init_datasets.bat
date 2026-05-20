@echo off
REM Initialize Missing Dataset Files for Bot 1
REM Run this once after model training to create required empty datasets

echo ========================================
echo Current Candle Bot - Dataset Initializer
echo ========================================
echo.

cd /d "%~dp0"

REM Activate virtual environment
call venv\Scripts\activate.bat

echo [1/4] Checking data directory...
if not exist "data" (
    mkdir data
    echo Created data\ directory
)

echo.
echo [2/4] Creating predictions_log.csv...
python -c "import pandas as pd; pd.DataFrame(columns=['timestamp_ms','symbol','interval','candle_open_time_ms','candle_close_time_ms','regime','prob_up','prob_down','prob_up_smoothed','threshold_bull','threshold_bear','strength_body_pct','range_pct','volume_pctile','cooldown_active','filters_passed','decision','reason']).to_csv('data/predictions_log.csv', index=False); print('✓ predictions_log.csv created')"

echo.
echo [3/4] Creating alerts_log.csv...
python -c "import pandas as pd; pd.DataFrame(columns=['timestamp_ms','symbol','interval','candle_open_time_ms','direction','confidence','regime','message_text']).to_csv('data/alerts_log.csv', index=False); print('✓ alerts_log.csv created')"

echo.
echo [4/4] Verifying files...
dir data\*.csv

echo.
echo ========================================
echo ✓ Dataset initialization complete!
echo ========================================
echo.
echo Next step: Run test_components.py
echo.

pause
