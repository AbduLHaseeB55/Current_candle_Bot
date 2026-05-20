# Current Candle Close Bot - Complete Setup Guide

## Overview

Bot 1 is a 24/7 BTCUSDT 15m candle close prediction system that uses deep learning (LSTM) to generate high-precision trading alerts via Telegram.

## Project Structure

```
current_candle_bot/
├── run_bot.py                  # Main bot runner
├── binance_stream.py           # WebSocket stream handler
├── features.py                 # Feature engineering
├── regime_detection.py         # Market regime detection
├── model_inference.py          # LSTM model inference
├── decision_engine.py          # Alert decision logic
├── telegram_notifier.py        # Telegram integration
├── dataset_writer.py           # Data persistence
├── .env.template               # Environment template
├── .env                        # Your credentials (create this)
├── requirements.txt            # Python dependencies
├── setup_env.bat               # Setup script
├── start_bot.bat               # Start bot (interactive)
├── start_bot_background.bat    # Start bot (background)
├── stop_bot.bat                # Stop bot
├── models/
│   └── current_candle_lstm.pt  # Trained model
├── artifacts/
│   └── thresholds.json         # Regime thresholds
├── data/
│   ├── candles_15m.csv         # Raw candle data
│   ├── predictions_log.csv     # Inference log
│   └── alerts_log.csv          # Alert log
├── logs/
│   └── inference.log           # Runtime logs
└── notebooks/
    └── model_training.ipynb    # Training notebook
```

## Installation Steps

### 1. Install Python

- Download Python 3.10+ from python.org
- During installation, check "Add Python to PATH"
- Verify: Open cmd and run `python --version`

### 2. Setup Virtual Environment

```batch
cd e:\haseeb\current_candle_bot
setup_env.bat
```

This will:
- Create a virtual environment
- Install all dependencies
- Set up the project

### 3. Configure Environment

```batch
copy .env.template .env
notepad .env
```

Fill in these required variables:

```
TELEGRAM_BOT_TOKEN=your_token_from_botfather
TELEGRAM_CHAT_ID=your_chat_id
SYMBOL=BTCUSDT
INTERVAL=15m
MODEL_PATH=models/current_candle_lstm.pt
```

**Getting Telegram Credentials:**

1. Talk to @BotFather on Telegram
   - Send `/newbot`
   - Follow instructions
   - Copy the token

2. Get your Chat ID:
   - Talk to @userinfobot
   - Copy the ID number

### 4. Train the Model

Open Jupyter notebook:

```batch
venv\Scripts\activate
jupyter notebook notebooks/model_training.ipynb
```

Run all cells to:
- Load/generate training data
- Build features
- Train LSTM model
- Evaluate performance
- Save model and thresholds

### 5. Test the Bot

```batch
start_bot.bat
```

Watch for:
- ✓ "Connected to Binance WebSocket"
- ✓ "Model loaded successfully"
- ✓ "Telegram connected and ready"
- ✓ Candles streaming

Press Ctrl+C to stop when satisfied.

## Running 24/7 on Windows

### Option 1: Task Scheduler (Recommended)

1. Open Task Scheduler
2. Create Task:
   - **Name**: Current Candle Bot
   - **Trigger**: At system startup
   - **Action**: Start a program
     - Program: `e:\haseeb\current_candle_bot\start_bot_background.bat`
   - **Settings**:
     - ☑ Run whether user is logged in or not
     - ☑ Run with highest privileges
     - ☑ If task fails, restart every 5 minutes

### Option 2: NSSM (Non-Sucking Service Manager)

1. Download NSSM: https://nssm.cc/download
2. Extract to a folder
3. Run as Administrator:

```batch
nssm install CurrentCandleBot
```

4. Configure:
   - Path: `e:\haseeb\current_candle_bot\venv\Scripts\python.exe`
   - Startup directory: `e:\haseeb\current_candle_bot`
   - Arguments: `run_bot.py`

5. Start service:

```batch
nssm start CurrentCandleBot
```

### Option 3: Simple Background Process

```batch
start_bot_background.bat
```

This runs the bot in the background. To stop:

```batch
stop_bot.bat
```

## Monitoring

### Check Logs

```batch
type logs\inference.log
```

Or use a log viewer like BareTail.

### Check Datasets

```batch
dir data
type data\alerts_log.csv
```

### Telegram Heartbeat

The bot sends a heartbeat message every hour to confirm it's running.

## Success Checklist

✓ Virtual environment created and activated
✓ All dependencies installed
✓ .env file configured with credentials
✓ Model trained and saved
✓ Bot connects to Binance WebSocket
✓ Model loads successfully
✓ Telegram connection verified
✓ First candle processed
✓ Predictions logged
✓ Alert sent (when conditions met)
✓ Datasets growing on disk

## Troubleshooting

### "Module not found" error

```batch
venv\Scripts\activate
pip install -r requirements.txt
```

### "Model file not found"

Run the training notebook first to create the model.

### Telegram connection failed

- Check `TELEGRAM_BOT_TOKEN` is correct
- Check `TELEGRAM_CHAT_ID` is correct
- Test by sending `/start` to your bot

### WebSocket disconnects

The bot automatically reconnects. Check your internet connection.

### No alerts being sent

This is normal! Alerts only fire when:
- Confidence > threshold (0.65+)
- Candle body > minimum (0.10%+)
- Volume > percentile (60+)
- Cooldown period passed (10 minutes)

### High memory usage

Normal for LSTM inference. Expect 500MB-1GB.

## Maintenance

### Daily

- Check `logs\inference.log` for errors
- Verify alerts are reasonable
- Monitor `data` folder size

### Weekly

- Review `alerts_log.csv` for precision
- Check `predictions_log.csv` for patterns
- Backup model and data folders

### Monthly

- Retrain model with new data
- Tune thresholds based on performance
- Update dependencies if needed

## Retraining

When you have enough new data:

1. Open training notebook
2. Load updated `data/candles_15m.csv`
3. Run all cells
4. Evaluate new model performance
5. If improved, it auto-saves to `models/current_candle_lstm.pt`
6. Restart bot to load new model

## Security

- Never commit `.env` to git
- Keep `TELEGRAM_BOT_TOKEN` secret
- Use `chmod 600` equivalent on Linux
- Rotate tokens if exposed

## Performance Tuning

### Increase Precision (fewer but better alerts)

In `.env`:
```
BULL_THRESHOLD=0.75
BEAR_THRESHOLD=0.75
MIN_BODY_PCT=0.0015
MIN_VOL_PCTILE=70
```

### Increase Recall (more alerts)

In `.env`:
```
BULL_THRESHOLD=0.60
BEAR_THRESHOLD=0.60
MIN_BODY_PCT=0.0008
MIN_VOL_PCTILE=50
```

## Support

Check logs first:
```batch
type logs\inference.log | find "ERROR"
```

Common issues are in Troubleshooting section above.

## Next Steps

Once Bot 1 is stable:
- Backtest performance
- Optimize thresholds per regime
- Add ensemble models
- Implement auto-retraining
- Deploy to cloud (optional)

---

**Created**: December 2024
**Version**: 1.0
**Status**: Production Ready
