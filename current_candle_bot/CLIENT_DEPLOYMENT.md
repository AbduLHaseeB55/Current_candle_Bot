# 🚀 CLIENT DELIVERY PACKAGE
## Current Candle Close Bot - Production Ready

---

## 📦 WHAT'S INCLUDED

### Core Application Files:
```
current_candle_bot/
├── run_bot.py                    # Main bot entry point
├── binance_stream.py             # WebSocket connection
├── features.py                   # Feature engineering
├── regime_detection.py           # Market regime classifier
├── model_inference.py            # LSTM model
├── decision_engine.py            # Alert filters
├── telegram_notifier.py          # Telegram integration
├── dataset_writer.py             # Data logging
├── requirements.txt              # Python dependencies
├── .env.template                 # Configuration template
├── models/
│   └── current_candle_lstm.pt   # Trained LSTM model
├── artifacts/
│   └── thresholds.json          # Regime thresholds
└── data/
    └── candles_15m.csv          # Historical data
```

---

## ⚙️ SERVER REQUIREMENTS

### Minimum:
- **OS**: Windows Server 2019+ OR Ubuntu 20.04+ OR Windows 10/11
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 10GB
- **Internet**: Stable connection (any speed)
- **Python**: 3.10 or higher

### Recommended (Your Vultr Setup):
- **CPU**: 8 vCPU
- **RAM**: 40GB
- **GPU**: A40 (optional, for faster retraining)
- **Storage**: NVMe SSD

---

## 📋 INSTALLATION GUIDE

### Step 1: Transfer Files to Server
```cmd
# Copy entire project folder to server
# Recommended path: C:\BotProjects\current_candle_bot (Windows)
#                   /opt/trading_bots/current_candle_bot (Linux)
```

### Step 2: Install Python Dependencies
```cmd
cd current_candle_bot
python -m venv venv
venv\Scripts\activate       # Windows
# OR
source venv/bin/activate    # Linux

pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
```cmd
# Copy template and edit
copy .env.template .env     # Windows
# OR
cp .env.template .env       # Linux

# Edit .env with your values:
# - TELEGRAM_BOT_TOKEN=your_bot_token
# - TELEGRAM_CHAT_ID=your_chat_id
```

### Step 4: Test Installation
```cmd
python test_components.py
# Should show all ✓ PASS
```

---

## 🔐 TELEGRAM SETUP (FOR CLIENT)

### Create Telegram Bot:
1. Open Telegram, search for **@BotFather**
2. Send `/newbot`
3. Follow prompts, get **BOT_TOKEN**
4. Copy token to `.env` file

### Get Chat ID:
1. Start conversation with your bot
2. Send any message
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Find `"chat":{"id":123456789}`
5. Copy chat ID to `.env` file

### Test Telegram:
```cmd
python -c "from telegram_notifier import TelegramNotifier; import asyncio; from dotenv import load_dotenv; import os; load_dotenv(); bot = TelegramNotifier(os.getenv('TELEGRAM_BOT_TOKEN'), os.getenv('TELEGRAM_CHAT_ID')); asyncio.run(bot.send_message('✅ Bot is connected!'))"
```

---

## 🔄 24/7 DEPLOYMENT OPTIONS

### OPTION A: Windows Server (Recommended for Windows)

#### Using Task Scheduler:
1. Open **Task Scheduler**
2. Create Basic Task → Name: "TradingBot"
3. Trigger: **At startup**
4. Action: **Start a program**
   - Program: `C:\BotProjects\current_candle_bot\venv\Scripts\python.exe`
   - Arguments: `run_bot.py`
   - Start in: `C:\BotProjects\current_candle_bot`
5. Settings:
   - ☑ Run whether user is logged on or not
   - ☑ Run with highest privileges
   - ☑ If task fails, restart every 5 minutes
6. Save and **Run** task

---

### OPTION B: Linux Server (Recommended for Ubuntu)

#### Using systemd Service:

**Create service file:**
```bash
sudo nano /etc/systemd/system/trading-bot.service
```

**Add this content:**
```ini
[Unit]
Description=Current Candle Trading Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/opt/trading_bots/current_candle_bot
Environment="PATH=/opt/trading_bots/current_candle_bot/venv/bin"
ExecStart=/opt/trading_bots/current_candle_bot/venv/bin/python run_bot.py
Restart=always
RestartSec=10
StandardOutput=append:/opt/trading_bots/current_candle_bot/logs/bot.log
StandardError=append:/opt/trading_bots/current_candle_bot/logs/bot_error.log

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
sudo systemctl status trading-bot
```

---

## 📊 MONITORING & MAINTENANCE

### Check Bot Status:

**Windows:**
```cmd
tasklist | findstr python.exe
```

**Linux:**
```bash
sudo systemctl status trading-bot
ps aux | grep run_bot.py
```

### View Live Logs:

**Windows:**
```cmd
powershell Get-Content logs\inference.log -Wait -Tail 20
```

**Linux:**
```bash
tail -f logs/inference.log
journalctl -u trading-bot -f
```

### Check Alerts Sent:
```cmd
type data\alerts_log.csv     # Windows
cat data/alerts_log.csv      # Linux
```

### Monitor Performance:
```cmd
# Check predictions
type data\predictions_log.csv | more

# Count alerts per day
python -c "import pandas as pd; df=pd.read_csv('data/alerts_log.csv'); print(df.groupby(pd.to_datetime(df['timestamp_ms'], unit='ms').dt.date).size())"
```

---

## 🛠️ TROUBLESHOOTING

### Bot Not Starting:
1. Check `.env` file exists and has correct values
2. Check logs: `logs/inference.log`
3. Verify Python version: `python --version` (must be 3.10+)
4. Reinstall dependencies: `pip install -r requirements.txt`

### No Telegram Alerts:
1. Check bot token is correct
2. Verify chat ID is correct
3. Ensure you sent `/start` to bot first
4. Check firewall allows outbound HTTPS
5. Test with test script (see Telegram Setup above)

### WebSocket Connection Drops:
- Bot auto-reconnects automatically
- Check internet connection
- May miss 1-2 candles during reconnection
- Normal behavior if occasional

### High False Alerts:
- Edit `.env`, increase thresholds:
  ```
  BULL_THRESHOLD=0.70
  BEAR_THRESHOLD=0.70
  MIN_BODY_PCT=0.0015
  ```
- Restart bot after changes

---

## 📈 PERFORMANCE EXPECTATIONS

### Normal Operation:
- **Alerts per day**: 5-15 (market dependent)
- **Alert precision**: 55-70% correct
- **CPU usage**: <5%
- **RAM usage**: ~500MB
- **Disk growth**: ~1MB per day

### Success Criteria:
- ✓ Bot runs continuously without crashes
- ✓ Receives candle data every 15 minutes
- ✓ Sends alerts only on strong signals
- ✓ No spam (cooldown working)
- ✓ Datasets growing steadily

---

## 🔄 UPDATES & RETRAINING

### Update Bot Code:
1. Stop bot
2. Replace Python files
3. Run `pip install -r requirements.txt`
4. Restart bot

### Retrain Model (Monthly Recommended):
1. Backup current model: `copy models\current_candle_lstm.pt models\backup\`
2. Run training notebook: `jupyter notebook notebooks/model_training.ipynb`
3. New model saves automatically
4. Restart bot to use new model

---

## 🆘 SUPPORT & MAINTENANCE

### Log Files Location:
- **Application logs**: `logs/inference.log`
- **Error logs**: `logs/inference_error.log`
- **Predictions**: `data/predictions_log.csv`
- **Alerts**: `data/alerts_log.csv`

### Regular Maintenance (Monthly):
1. Review alert precision (target: >55%)
2. Check disk space (clean old logs if needed)
3. Update thresholds if too many/few alerts
4. Consider retraining if market regime changed

### Emergency Stop:
**Windows:**
```cmd
taskkill /F /IM python.exe
# OR disable Task Scheduler task
```

**Linux:**
```bash
sudo systemctl stop trading-bot
```

---

## ✅ DELIVERY CHECKLIST

Before handing over to client, verify:

- [ ] All files transferred to server
- [ ] Python 3.10+ installed
- [ ] Dependencies installed (`requirements.txt`)
- [ ] `.env` configured with Telegram credentials
- [ ] Test components pass (`test_components.py`)
- [ ] Telegram test message received
- [ ] 24/7 service configured (Task Scheduler or systemd)
- [ ] Bot running and making predictions
- [ ] Logs accessible and readable
- [ ] Client has access to server
- [ ] Client knows how to:
  - [ ] Check bot status
  - [ ] View logs
  - [ ] Restart bot
  - [ ] Adjust thresholds
  - [ ] Contact support

---

## 📞 CLIENT TRAINING CHECKLIST

Ensure client knows:
1. ✓ How to check if bot is running
2. ✓ Where to view logs
3. ✓ How to read Telegram alerts
4. ✓ What metrics indicate good performance
5. ✓ How to restart bot if needed
6. ✓ How to adjust alert thresholds
7. ✓ When to request retraining
8. ✓ Who to contact for support

---

## 📄 DOCUMENTATION PROVIDED

Include these files in delivery:
- ✓ This deployment guide (CLIENT_DEPLOYMENT.md)
- ✓ Quick start guide (EXECUTE_THIS.md)
- ✓ Requirements checklist (REQUIREMENTS_CHECKLIST.md)
- ✓ Project summary (PROJECT_SUMMARY.md)
- ✓ Troubleshooting guide (POST_TRAINING_GUIDE.md)

---

## 🎯 FINAL NOTES

**This bot is production-ready when:**
- Runs continuously for 7+ days without intervention
- Sends 5-15 alerts per day (market dependent)
- Alert precision >55% (measured over 1 week)
- No spam during flat market hours
- Auto-restarts on failure
- Datasets growing correctly

**Client should expect:**
- Not every alert will be profitable (55-70% accuracy is realistic)
- Fewer alerts during sideways/choppy markets (by design)
- More alerts during trending markets
- Occasional missed candles due to network issues (auto-recovers)

---

**Deployment Date**: [Fill in date]
**Bot Version**: 1.0
**Model Training Date**: [Fill in from training_runs.jsonl]
**Support Contact**: [Your contact info]

---

**Status**: ✅ PRODUCTION READY
