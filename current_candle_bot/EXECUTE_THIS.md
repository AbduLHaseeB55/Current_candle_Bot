# 🚀 QUICK START - Execute These Commands In Order

## You've completed model training. Here's what to do next:

---

## ⚡ 5-STEP DEPLOYMENT (30 minutes total)

### STEP 1: Initialize Missing Datasets (2 min)
```cmd
cd e:\Haseeb\current_candle_bot\current_candle_bot
init_datasets.bat
```
**Creates**: `predictions_log.csv` and `alerts_log.csv`

---

### STEP 2: Validate Everything (5 min)
```cmd
venv\Scripts\activate
python validate_deployment.py
```
**Expected**: All checks should show ✓ PASS

**If any FAIL**, fix before proceeding:
- Missing dependencies → `pip install -r requirements.txt`
- Wrong .env values → Edit `.env` file
- Missing files → Check error messages

---

### STEP 3: Test Components (5 min)
```cmd
python test_components.py
```
**Expected**: 
- ✓ All imports successful
- ✓ FeatureEngine works
- ✓ ModelInference loads model
- ✓ TelegramNotifier sends test message ← **CHECK YOUR TELEGRAM**

---

### STEP 4: Quick Live Test (5-10 min)
```cmd
quick_test.bat
```
**OR manually:**
```cmd
python run_bot.py
```
Let it run for 5-10 minutes, then press `Ctrl+C`.

**Watch for**:
- ✓ "Connected to Binance WebSocket"
- ✓ "Candle buffer warming up"
- ✓ No errors/tracebacks

**Check**: `logs\inference.log` for any issues

---

### STEP 5: Deploy 24/7 (Choose One)

#### Option A: Background Process (Simple)
```cmd
start_bot_background.bat
```
To stop later: `stop_bot.bat`

#### Option B: Task Scheduler (Recommended)
1. Open **Task Scheduler** (Windows Start → search "Task Scheduler")
2. **Create Basic Task** → Name: "CurrentCandleBot"
3. **Trigger**: At startup
4. **Action**: Start program
   - Program: `e:\Haseeb\current_candle_bot\current_candle_bot\venv\Scripts\python.exe`
   - Arguments: `run_bot.py`
   - Start in: `e:\Haseeb\current_candle_bot\current_candle_bot`
5. **Settings**:
   - ☑ Run whether user is logged on or not
   - ☑ If task fails, restart every 5 minutes
6. Right-click task → **Run** to start now

---

## ✅ HOW TO KNOW IT'S WORKING

### Within 5 minutes:
- [ ] Check Task Manager → `python.exe` is running
- [ ] Check `logs\inference.log` → see "Connected to Binance"
- [ ] No error messages repeating

### After 1 hour (4 candles):
- [ ] `data\predictions_log.csv` has 4 rows
- [ ] `data\candles_15m.csv` is growing
- [ ] Telegram received 0-2 alerts (depends on market)

### After 24 hours:
- [ ] `predictions_log.csv` has ~96 rows (one per 15 min)
- [ ] `alerts_log.csv` has 3-15 rows (precision-filtered alerts)
- [ ] Bot still running (check Task Manager)
- [ ] No repeated errors in logs

---

## 📊 MONITORING COMMANDS

### View Live Logs
```cmd
powershell Get-Content logs\inference.log -Wait -Tail 50
```

### Check Latest Predictions
```cmd
type data\predictions_log.csv | more
```

### Check Alerts Sent
```cmd
type data\alerts_log.csv
```

### Check Bot Status
```cmd
tasklist | findstr python.exe
```

---

## 🛠️ TROUBLESHOOTING

### Bot exits immediately
```cmd
type logs\inference.log
```
Look for error at bottom. Common causes:
- Model file missing/corrupted
- .env variable missing
- Wrong Python version

### No Telegram alerts
**Normal!** Bot only alerts on strong signals.

Check `predictions_log.csv` to see why:
- `decision=NO_ALERT` is correct behavior
- Look at `reason` column: "weak_body", "low_volume", "cooldown"

If you want more alerts, edit `.env`:
- Lower `BULL_THRESHOLD=0.60`
- Lower `MIN_BODY_PCT=0.0008`

### WebSocket disconnects
**Normal occasional drops.** Bot auto-reconnects.

If constant disconnects:
- Check internet connection
- Check Windows Firewall settings
- Binance may be rate-limiting (wait 5 min)

---

## ⚙️ TUNING (After 24-48 hours)

### Too Many Alerts (Spam)
Edit `.env` and increase:
```
BULL_THRESHOLD=0.70
BEAR_THRESHOLD=0.70
MIN_BODY_PCT=0.0015
MIN_VOL_PCTILE=70
COOLDOWN_MINUTES=15
```

### Too Few Alerts (Missing Opportunities)
Edit `.env` and decrease:
```
BULL_THRESHOLD=0.60
BEAR_THRESHOLD=0.60
MIN_BODY_PCT=0.0008
MIN_VOL_PCTILE=50
```

**After each change:**
1. Stop bot (Ctrl+C or stop_bot.bat)
2. Edit .env
3. Restart bot
4. Monitor for 24 hours

---

## 📋 FILES YOU NOW HAVE

### Core Bot
- `run_bot.py` ← Main entry point
- `binance_stream.py` ← WebSocket connection
- `features.py` ← Feature engineering
- `regime_detection.py` ← Market regime classifier
- `model_inference.py` ← LSTM model
- `decision_engine.py` ← Alert filters
- `telegram_notifier.py` ← Telegram integration
- `dataset_writer.py` ← Data persistence

### Configuration
- `.env` ← All settings
- `artifacts/thresholds.json` ← Regime thresholds

### Model & Data
- `models/current_candle_lstm.pt` ← Trained model
- `data/candles_15m.csv` ← Historical + live candles
- `data/predictions_log.csv` ← Inference audit trail
- `data/alerts_log.csv` ← Sent alerts log
- `data/training_runs.jsonl` ← Training metadata

### Helper Scripts
- `init_datasets.bat` ← Create dataset files
- `validate_deployment.py` ← Pre-flight check
- `test_components.py` ← Component tests
- `quick_test.bat` ← 5-minute test
- `start_bot_background.bat` ← Start 24/7
- `stop_bot.bat` ← Stop background bot

### Documentation (NEW)
- `POST_TRAINING_GUIDE.md` ← Detailed deployment guide
- `REQUIREMENTS_CHECKLIST.md` ← Requirements validation
- `EXECUTE_THIS.md` ← **THIS FILE - Your quick reference**

---

## 🎯 SUCCESS CRITERIA

Your bot is **working correctly** when:

✓ Runs 24/7 without manual intervention  
✓ Sends 3-15 alerts per day (market-dependent)  
✓ Alert win rate >55% (check manually for now)  
✓ No spam during flat market hours  
✓ Logs show continuous operation  
✓ Datasets growing steadily  

---

## 📞 FINAL CHECKLIST

Before closing this document, confirm:

- [ ] Ran `init_datasets.bat`
- [ ] Ran `validate_deployment.py` → All PASS
- [ ] Ran `test_components.py` → All ✓
- [ ] Tested bot for 5-10 minutes → No errors
- [ ] Received Telegram test message
- [ ] Started 24/7 deployment (Task Scheduler or background)
- [ ] Verified bot is running (Task Manager)
- [ ] Can access logs (inference.log)
- [ ] Understand how to tune thresholds

---

## 🚀 YOU'RE DONE!

**Your bot is now:**
- ✓ Trained on 200k historical candles
- ✓ Configured with precision-first filters
- ✓ Connected to Binance live stream
- ✓ Sending Telegram alerts on strong signals
- ✓ Logging all data for future improvements
- ✓ Running 24/7

**Next milestone**: Let it run for 1 week, measure precision, tune thresholds.

**After that**: Consider ensemble models, next-candle predictions (Bot 2 architecture).

---

## Need Help?

1. Read error in `logs\inference.log`
2. Check `REQUIREMENTS_CHECKLIST.md` for detailed status
3. Re-run `validate_deployment.py`
4. Review `POST_TRAINING_GUIDE.md` for troubleshooting

**You've completed the project! Now just execute Steps 1-5 above.** 🎉
