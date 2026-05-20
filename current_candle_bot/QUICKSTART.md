# Quick Start Guide - Current Candle Bot

## 5-Minute Setup

### Step 1: Setup Environment (2 minutes)

```batch
cd e:\haseeb\current_candle_bot
setup_env.bat
```

Wait for installation to complete.

### Step 2: Configure Credentials (1 minute)

```batch
copy .env.template .env
notepad .env
```

Add your Telegram credentials:
- `TELEGRAM_BOT_TOKEN` - Get from @BotFather
- `TELEGRAM_CHAT_ID` - Get from @userinfobot

Save and close.

### Step 3: Train Model (2 minutes)

```batch
venv\Scripts\activate
jupyter notebook
```

Open `notebooks/model_training.ipynb` and click "Run All"

### Step 4: Start Bot

```batch
start_bot.bat
```

Done! Bot is now running.

## Expected Output

```
============================================================
CURRENT CANDLE CLOSE BOT - STARTING
============================================================
Symbol: BTCUSDT
Interval: 15m
Model: models/current_candle_lstm.pt
============================================================
Loading model...
Model loaded: {'loaded': True, ...}
Verifying Telegram connection...
✅ Bot connected and ready!
Telegram connected successfully!
Starting main loop...
Connected to Binance WebSocket: wss://stream.binance.com:9443/ws/btcusdt@kline_15m
```

## Testing

After 15 minutes (one candle closes), you should see:

```
Closed candle received: BTCUSDT O:50123.45 H:50234.56 L:50098.23 C:50198.34
Regime: TREND, Metrics: {'adx': 32.5, 'vol_pctile': 65.3, ...}
Model output: P(UP)=0.7234, P(UP_smoothed)=0.7156
Decision: ALERT_BULL, Reason: passed_all_filters
🚨 ALERT SENT: BULL @ 71.6%
```

And you'll receive a Telegram message!

## Common Issues

**"Virtual environment not found"**
→ Run `setup_env.bat` first

**"Model file not found"**
→ Train the model using the notebook

**"Telegram connection failed"**
→ Check your bot token and chat ID in `.env`

**"No alerts after 1 hour"**
→ Normal! Bot is precision-first. Alerts are rare but high-quality.

## Stop Bot

Press `Ctrl+C` in the console, or run:

```batch
stop_bot.bat
```

## Run 24/7

Use Task Scheduler:
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: At startup
4. Action: `e:\haseeb\current_candle_bot\start_bot_background.bat`
5. Done!

## Check Status

View logs:
```batch
type logs\inference.log
```

View alerts:
```batch
type data\alerts_log.csv
```

## Support

See `README.md` for full documentation.

---

**That's it! Your bot is now predicting candle closes 24/7!** 🚀
