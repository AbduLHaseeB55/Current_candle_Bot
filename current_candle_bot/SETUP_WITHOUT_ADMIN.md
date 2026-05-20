# 🔓 24/7 SETUP WITHOUT ADMIN RIGHTS

## ⚡ **OPTION 1: Automatic Setup (Easiest)**

### Run this script:
```cmd
setup_24_7_no_admin.bat
```

**What it does:**
- ✓ Creates Windows Startup shortcut (starts at login)
- ✓ Creates manual start script
- ✓ Starts bot immediately
- ✓ **No admin rights needed!**

**Bot will start automatically when you log in to Windows**

---

## ⚡ **OPTION 2: Manual Task Scheduler (If You Have Admin)**

### Step 1: Open Task Scheduler
```
Win + R → type: taskschd.msc → Enter
```

### Step 2: Create Basic Task
1. Click "**Create Basic Task**" (right panel)
2. **Name**: `TradingBot`
3. **Trigger**: "When I log on"
4. **Action**: "Start a program"
   - **Program**: `e:\Haseeb\current_candle_bot\current_candle_bot\venv\Scripts\python.exe`
   - **Arguments**: `run_bot.py`
   - **Start in**: `e:\Haseeb\current_candle_bot\current_candle_bot`
5. Click **Finish**

### Step 3: Configure Settings
1. Right-click task → **Properties**
2. **Settings tab**:
   - ☑ If task fails, restart every: **5 minutes**
   - ☑ Attempt to restart up to: **3 times**
3. Click **OK**

### Step 4: Test
```cmd
# Right-click task in Task Scheduler → Run
tasklist | findstr python.exe
```

---

## ⚡ **OPTION 3: Keep Terminal Open (Simple)**

### Just run:
```cmd
cd e:\Haseeb\current_candle_bot\current_candle_bot
venv\Scripts\activate
python run_bot.py
```

**Keep this terminal window open**

**Pros:**
- ✓ Simple, works immediately
- ✓ See logs in real-time
- ✓ No setup needed

**Cons:**
- ✗ Stops if you close terminal
- ✗ Stops if you log out
- ✗ Not truly 24/7

---

## ⚡ **OPTION 4: Background Process (Windows Service Alternative)**

### Create persistent start script:

**File: `start_bot_persistent.bat`**
```batch
@echo off
cd /d e:\Haseeb\current_candle_bot\current_candle_bot
:RESTART
echo Starting bot at %date% %time%
venv\Scripts\python.exe run_bot.py
echo Bot stopped at %date% %time%, restarting in 5 seconds...
timeout /t 5 /nobreak
goto RESTART
```

**Run it:**
```cmd
start /B start_bot_persistent.bat
```

**This will:**
- ✓ Run in background
- ✓ Auto-restart if crashes
- ✓ Keeps restarting forever
- ✗ Stops if you reboot (unless in Startup folder)

---

## 🎯 **RECOMMENDED SOLUTION FOR YOU**

Since you can't run as admin, use **OPTION 1**:

```cmd
cd e:\Haseeb\current_candle_bot\current_candle_bot
setup_24_7_no_admin.bat
```

**This creates:**
1. **Startup shortcut** → Auto-starts at login
2. **start_bot_now.bat** → Manual start anytime
3. Bot starts immediately

---

## ✅ **VERIFY IT'S RUNNING**

### Check bot is running:
```cmd
tasklist | findstr python.exe
```

**Expected output:**
```
python.exe    12345  Console   1   150,000 K
```

### View live logs:
```cmd
powershell Get-Content logs\inference.log -Wait -Tail 20
```

### Stop bot:
```cmd
taskkill /F /IM python.exe
```

### Start bot again:
```cmd
start_bot_now.bat
```

---

## 📍 **STARTUP SHORTCUT LOCATION**

Your startup shortcut will be here:
```
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\TradingBot.lnk
```

**To remove auto-start:** Delete this shortcut

---

## 🆘 **TROUBLESHOOTING**

### Bot doesn't start at login:
1. Check shortcut exists:
   ```cmd
   dir "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\"
   ```
2. Should see `TradingBot.lnk`
3. Double-click it manually to test

### Bot stops after few hours:
- Windows might be putting computer to sleep
- Go to: **Control Panel → Power Options → Change plan settings**
- Set "Put computer to sleep" to **Never**

### Need true 24/7 without staying logged in:
- You'll need admin rights for Task Scheduler
- Ask server administrator to create the task
- Or use the Linux deployment if possible

---

## 💡 **FOR CLIENT DELIVERY**

**If client server has admin access:**
- They can run `setup_24_7.bat` as administrator
- Gets full Task Scheduler task with auto-restart

**If client server no admin:**
- They run `setup_24_7_no_admin.bat`
- Bot starts at login (good enough for most cases)

**If Linux server:**
- They run `deploy_linux.sh` with sudo
- Gets full systemd service (best option)

---

## ✅ **QUICK START (RIGHT NOW)**

```cmd
# Run this ONE command:
setup_24_7_no_admin.bat
```

**That's it! Bot will now start every time you log in.**

---

**Need help?** Check if bot is running:
```cmd
tasklist | findstr python.exe
```

See logs:
```cmd
type logs\inference.log
```
