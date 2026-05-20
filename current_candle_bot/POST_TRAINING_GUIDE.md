# Post-Training Deployment Guide
## Current Candle Close Bot - BTCUSDT 15m

---

## ✅ Current Status (What You've Completed)

- ✓ **Historical data fetched**: ~200k records since 2019
- ✓ **Model trained**: `models/current_candle_lstm.pt`
- ✓ **Thresholds configured**: `artifacts/thresholds.json`
- ✓ **Training metadata**: `data/training_runs.jsonl`
- ✓ **Environment configured**: `.env` with Telegram credentials
- ✓ **All core modules**: Present and ready

---

## 📋 What You Need to Do Next (Step-by-Step)

### **PHASE 1: Pre-Flight Validation (15 minutes)**

#### Step 1.1 - Verify All Components
```cmd
cd e:\Haseeb\current_candle_bot\current_candle_bot
venv\Scripts\activate
python test_components.py
```

**Expected Output:**
- ✓ All imports successful
- ✓ FeatureEngine works
- ✓ RegimeDetector works
- ✓ ModelInference loads model
- ✓ DecisionEngine filters working
- ✓ TelegramNotifier can send test message
- ✓ DatasetWriter creates files

**If any test fails:** Check error messages carefully. Most common issues:
- Missing dependencies: `pip install -r requirements.txt`
- Wrong Python version: Need Python 3.10+
- Model file corrupted: Check file size

---

#### Step 1.2 - Create Missing Dataset Files

**Check what exists:**
```cmd
dir data\
```

**Required files:**
- ✓ `candles_15m.csv` (you have this)
- ✓ `training_runs.jsonl` (you have this)
- ✗ `predictions_log.csv` (create empty)
- ✗ `alerts_log.csv` (create empty)

**Action:** Run this to create missing datasets:
```cmd
python -c "import pandas as pd; pd.DataFrame(columns=['timestamp_ms','symbol','interval','candle_open_time_ms','candle_close_time_ms','regime','prob_up','prob_down','prob_up_smoothed','threshold_bull','threshold_bear','strength_body_pct','range_pct','volume_pctile','cooldown_active','filters_passed','decision','reason']).to_csv('data/predictions_log.csv', index=False)"

python -c "import pandas as pd; pd.DataFrame(columns=['timestamp_ms','symbol','interval','candle_open_time_ms','direction','confidence','regime','message_text']).to_csv('data/alerts_log.csv', index=False)"
```

---

### **PHASE 2: Test Live Connection (10 minutes)**

#### Step 2.1 - Test Binance WebSocket (Dry Run)

Create a quick test script to verify Binance connection:

```cmd
python -c "import asyncio; from binance_stream import BinanceKlineStream; asyncio.run(BinanceKlineStream('BTCUSDT', '15m').test_connection())"
```

**Expected Output:**
- Connected to Binance WebSocket
- Receiving candle data
- Messages show proper format

**Note:** This should run for ~30 seconds then exit. If it hangs or errors, check internet connection.

---

#### Step 2.2 - Test Telegram Bot

```cmd
python -c "from telegram_notifier import TelegramNotifier; from dotenv import load_dotenv; import os; load_dotenv(); bot = TelegramNotifier(os.getenv('TELEGRAM_BOT_TOKEN'), os.getenv('TELEGRAM_CHAT_ID')); import asyncio; asyncio.run(bot.send_message('🤖 Bot is ALIVE - Test message from Current Candle Bot'))"
```

**Expected Output:**
- Message sent successfully
- Check your Telegram - you should receive the test message

**If fails:**
- Verify `TELEGRAM_BOT_TOKEN` in `.env`
- Verify `TELEGRAM_CHAT_ID` in `.env`
- Start a conversation with your bot first (send /start)

---

### **PHASE 3: Short Test Run (30-60 minutes)**

#### Step 3.1 - Run Bot in Foreground (Test Mode)

**Purpose:** Watch it live to catch any issues before 24/7 deployment.

```cmd
cd e:\Haseeb\current_candle_bot\current_candle_bot
venv\Scripts\activate
python run_bot.py
```

**What to Watch For:**

**✓ Good Signs (first 5 minutes):**
- `Connected to Binance WebSocket`
- `Candle buffer warming up (X/64 candles)`
- No repeated errors/tracebacks
- After 64 candles: `Buffer ready, starting predictions`

**✓ Good Signs (after warmup):**
- Every 15 minutes: new candle logged
- Predictions computed: `prob_up=0.XX, regime=TREND`
- Filters logged: `body_ok=True, volume_ok=False, decision=NO_ALERT`
- Telegram alerts ONLY when all filters pass

**✗ Red Flags:**
- Connection drops repeatedly
- `TypeError` or `KeyError` in feature computation
- Every candle triggers alert (spam)
- No candles arriving after 20 minutes

**Let it run for 1-2 hours** (4-8 candles) to verify stability.

Press `Ctrl+C` to stop gracefully when satisfied.

---

#### Step 3.2 - Verify Datasets Are Growing

After 1-2 hours, check:

```cmd
type data\predictions_log.csv | more
type data\alerts_log.csv | more
```

**Expected:**
- `predictions_log.csv` has rows (one per closed candle)
- `alerts_log.csv` may be empty (if no strong signals)
- Check file sizes are increasing

---

### **PHASE 4: Production Deployment (Windows)**

#### Step 4.1 - Create Windows Task Scheduler Entry (24/7 Runner)

Since you're on Windows (not Ubuntu systemd), use **Task Scheduler** for 24/7 operation.

**Option A: Use the provided batch scripts**

Check if these scripts exist:
- `start_bot.bat` - runs bot in foreground
- `start_bot_background.bat` - runs bot in background
- `stop_bot.bat` - stops background bot

**To run 24/7 in background:**
```cmd
start_bot_background.bat
```

**To stop:**
```cmd
stop_bot.bat
```

---

**Option B: Create Task Scheduler entry (recommended for true 24/7)**

1. Open **Task Scheduler** (Windows key → type "Task Scheduler")
2. Click **Create Basic Task**
3. Name: `CurrentCandleBot`
4. Trigger: **At startup**
5. Action: **Start a program**
   - Program/script: `e:\Haseeb\current_candle_bot\current_candle_bot\venv\Scripts\python.exe`
   - Arguments: `run_bot.py`
   - Start in: `e:\Haseeb\current_candle_bot\current_candle_bot`
6. Check **"Run whether user is logged on or not"**
7. Check **"Run with highest privileges"**
8. In **Settings** tab:
   - Check **"If task fails, restart every: 5 minutes"**
   - Check **"Stop task if runs longer than: disabled"**

**Start manually first time:**
- Right-click task → Run

---

#### Step 4.2 - Monitor Production Logs

**View live logs:**
```cmd
powershell Get-Content logs\inference.log -Wait -Tail 50
```

**Or open in text editor and refresh periodically.**

**What to monitor daily (first week):**
- Check `logs\inference.log` - no repeated errors
- Check `data\alerts_log.csv` - precision of alerts
- Check Telegram - are alerts useful?
- Check `data\predictions_log.csv` - decision reasons

---

### **PHASE 5: Validation Checklist (Day 1-7)**

After 24 hours, validate:

#### ✓ **Operational Health**
- [ ] Bot still running (check Task Manager for python.exe)
- [ ] No crash loops (check Task Scheduler history)
- [ ] Logs show continuous candle stream
- [ ] No "Out of memory" or resource errors

#### ✓ **Alert Quality**
- [ ] Received at least 1-5 alerts (if market moved)
- [ ] Alerts were NOT spam (check if direction was correct)
- [ ] No alerts during flat/sideways hours (good!)
- [ ] Alert messages are readable and useful

#### ✓ **Data Integrity**
- [ ] `candles_15m.csv` growing (one row per 15 min)
- [ ] `predictions_log.csv` growing (one row per 15 min)
- [ ] `alerts_log.csv` has entries only when alerted
- [ ] No duplicate rows (check `candle_open_time_ms`)

#### ✓ **Performance Metrics (Week 1)**
Calculate from `alerts_log.csv`:
- **Alert frequency**: X alerts per day
- **Win rate**: % of alerts where direction was correct
- **False positive rate**: % of alerts during flat candles

**Acceptance criteria:**
- Alert frequency: 3-15 per day (not 0, not 100)
- Win rate: >55% (better than random)
- No spam during dead hours

---

### **PHASE 6: Fine-Tuning (Week 2+)**

If you see issues, adjust `.env`:

**Too many alerts (spam):**
- Increase `BULL_THRESHOLD` / `BEAR_THRESHOLD` (try 0.70-0.75)
- Increase `MIN_BODY_PCT` (try 0.0015-0.0020)
- Increase `MIN_VOL_PCTILE` (try 70-80)
- Increase `COOLDOWN_MINUTES` (try 15-20)

**Too few alerts (missed opportunities):**
- Decrease thresholds (try 0.60-0.62)
- Decrease `MIN_BODY_PCT` (try 0.0008)
- Check regime thresholds in `artifacts/thresholds.json`

**After each change:**
1. Stop bot
2. Edit `.env`
3. Restart bot
4. Monitor for 24-48 hours

---

## 🛠️ Troubleshooting Common Issues

### Issue: Bot starts but exits immediately
**Fix:**
- Check `.env` has all required variables
- Check model file exists: `models/current_candle_lstm.pt`
- Check logs: `logs\inference.log`

### Issue: WebSocket connection drops
**Fix:**
- Check internet connection
- Binance may have rate limits (wait 1 minute, restart)
- Check Windows Firewall isn't blocking

### Issue: No Telegram alerts
**Fix:**
- Check filters in `predictions_log.csv` (see why `decision=NO_ALERT`)
- Most common: `volume_ok=False` or `body_too_small`
- Adjust thresholds if too strict

### Issue: Every candle triggers alert (spam)
**Fix:**
- Thresholds too low or filters disabled
- Check `MIN_BODY_PCT` > 0.0010
- Check `BULL_THRESHOLD` >= 0.65
- Check `COOLDOWN_MINUTES` >= 10

### Issue: Model predictions always 0.5
**Fix:**
- Model not loaded correctly
- Check model file is not corrupted
- Check model was trained properly
- Re-run training if needed

---

## 📊 Success Metrics (What "Working" Looks Like)

### Day 1:
- ✓ Bot runs for 24 hours without crashing
- ✓ Received 3-10 Telegram alerts
- ✓ Logs show continuous operation
- ✓ Datasets are populated

### Week 1:
- ✓ Alert win rate >55%
- ✓ No spam during flat market hours
- ✓ False positive rate <30%
- ✓ Datasets have 7 days of data

### Month 1:
- ✓ Zero manual interventions needed
- ✓ Alert precision improving
- ✓ Ready for ensemble upgrade (Bot 2)
- ✓ Sufficient data for retraining

---

## 🔄 Next Steps (Future Enhancements)

Once Bot 1 is stable (2-4 weeks):

1. **Add predictions for next candle** (Bot 2 architecture)
2. **Implement ensemble** (multiple models voting)
3. **Set up automated retraining** (weekly or daily)
4. **Add backtesting dashboard** (validate threshold changes)
5. **Implement advanced regime detection** (macro indicators)
6. **Deploy to cloud** (Azure/AWS for better uptime)

---

## 📞 Support / Validation

If something doesn't work:
1. Check logs first: `logs\inference.log`
2. Check datasets: Look for empty or missing files
3. Run `test_components.py` again
4. Verify `.env` has no typos

**You've completed 90% of the project. The remaining 10% is testing, monitoring, and tuning.**

---

## Quick Command Reference

```cmd
# Activate environment
cd e:\Haseeb\current_candle_bot\current_candle_bot
venv\Scripts\activate

# Test components
python test_components.py

# Run bot (foreground)
python run_bot.py

# Run bot (background - Windows)
start_bot_background.bat

# Stop bot (background)
stop_bot.bat

# View logs (live)
powershell Get-Content logs\inference.log -Wait -Tail 50

# Check datasets
type data\predictions_log.csv | more
type data\alerts_log.csv | more
```

---

**Ready to deploy? Start with PHASE 1 and work through each phase methodically. Good luck! 🚀**
