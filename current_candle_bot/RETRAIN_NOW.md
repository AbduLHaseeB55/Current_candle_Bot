# 🚀 Quick Retraining Guide

## ✅ Option 2 Implemented - Ready to Retrain

Your training notebook has been **fixed** to predict the NEXT candle and eliminate data leakage.

---

## 📋 Steps to Retrain (30-60 minutes)

### 1. **Start Jupyter Notebook**
```cmd
cd e:\Haseeb\current_candle_bot\current_candle_bot
venv\Scripts\activate
jupyter notebook
```

Browser will open automatically.

---

### 2. **Open Training Notebook**
- Click: `notebooks/model_training.ipynb`

---

### 3. **Run All Cells**
Click: **Cell → Run All**

Or run each cell with `Shift+Enter`

---

### 4. **Watch for These Messages**

#### ✅ Good Signs:
```
✓ FIXED: Predicting NEXT candle (no data leakage)
  Features from 64 candles → Label from candle 65

Training accuracy: 0.55-0.62 (not 1.0)
Validation accuracy: 0.52-0.60 (not 1.0)
Brier Score: 0.18 (not 0.0000)
```

#### ❌ Red Flags:
```
Training accuracy: 0.99-1.0  ← Still broken!
Validation accuracy: 1.0     ← Still broken!
Brier Score: 0.0000          ← Still broken!
```

If you see red flags, something went wrong. Contact me.

---

### 5. **Verify Confusion Matrix**

Should look like this:
```
            Predicted
           Red   Green
Actual Red  8000  2000   ← Has errors
     Green  2500  7500   ← Has errors
```

**NOT like this:**
```
            Predicted
           Red   Green
Actual Red  10000   0    ← Perfect (bad!)
     Green     0  10000  ← Perfect (bad!)
```

---

### 6. **Deploy New Model**

Model automatically saves to:
```
models/current_candle_lstm.pt
```

Restart your bot:
```cmd
# Stop current bot (Ctrl+C)
python run_bot.py
```

Bot will automatically load the new model.

---

## 📊 Expected Results

### Training Metrics:
- **Accuracy**: 52-62% ✓
- **Precision**: 55-65% ✓
- **Recall**: 50-60% ✓
- **F1-Score**: 0.52-0.62 ✓
- **Brier Score**: 0.15-0.25 ✓
- **AUC**: 0.55-0.65 ✓

### Live Predictions:
```
Model output: P(UP)=0.23  ← Good (varied)
Model output: P(UP)=0.67  ← Good (varied)
Model output: P(UP)=0.45  ← Good (varied)
```

**NOT:**
```
Model output: P(UP)=0.00  ← Bad (binary)
Model output: P(UP)=1.00  ← Bad (binary)
```

---

## ⚠️ Troubleshooting

### "NameError: FeatureEngine not found"
```cmd
# Make sure you're in the right directory
cd e:\Haseeb\current_candle_bot\current_candle_bot
jupyter notebook
```

### "CUDA out of memory"
Edit the notebook, find this line:
```python
batch_size = 32
```
Change to:
```python
batch_size = 16  # Smaller batch
```

### "Training takes too long"
Reduce epochs:
```python
num_epochs = 50
```
Change to:
```python
num_epochs = 20  # Faster
```

---

## 🎯 Success Criteria

After retraining, you should see:

✅ **Training completed** (no errors)
✅ **Accuracy 50-65%** (not 100%)
✅ **Model saved** to `models/current_candle_lstm.pt`
✅ **Confusion matrix** has errors (not perfect)
✅ **Live predictions** are varied (0.2-0.8 range)

---

## 📝 What Changed?

**Old (Broken):**
```
Features[64] → Label[64]  ← Leakage (features contain answer)
Accuracy: 100%            ← Too good to be true
```

**New (Fixed):**
```
Features[64] → Label[65]  ← No leakage (predicting future)
Accuracy: 55%             ← Realistic
```

---

## 🚀 After Retraining

1. **Stop old bot**: `Ctrl+C`
2. **Start new bot**: `python run_bot.py`
3. **Monitor for 1 week**: Check `data/predictions_log.csv`
4. **Measure accuracy**: Count correct vs total alerts
5. **Expected**: 55-65% real accuracy

---

## 📞 Need Help?

If anything goes wrong:
1. Check `TRAINING_FIX_CHANGELOG.md` for details
2. Verify all cells ran without errors
3. Check confusion matrix has errors (not perfect)
4. Ensure model file exists: `models/current_candle_lstm.pt`

---

**You're ready to retrain! Just run the notebook.** 🎉

*Estimated time: 30-60 minutes*
