# Data Requirements & Training Guide

## How Much Data Do You Need?

### Minimum Requirements (For Basic Model)
- **6 months** of data (~17,280 candles)
- **Time to collect**: ~4 minutes
- **File size**: ~2.5 MB
- **Use case**: Quick testing, proof of concept

### Recommended (For Good Performance)
- **1-2 years** of data (~35,000-70,000 candles)
- **Time to collect**: ~9-18 minutes
- **File size**: ~5-10 MB
- **Use case**: Production model with decent regime coverage

### Optimal (For Best Performance)
- **3+ years** of data (~100,000+ candles)
- **Time to collect**: ~25-30 minutes
- **File size**: ~15+ MB
- **Use case**: Maximum regime diversity, best generalization

## Why More Data Matters

### Regime Coverage
Your model needs to see different market conditions:
- **Bull markets** (trending up)
- **Bear markets** (trending down)
- **Sideways markets** (choppy)
- **High volatility** periods
- **Low volatility** periods

**3 years of data ensures all regimes are represented!**

### Training/Validation/Test Split
- Training: 70% (e.g., 70,000 candles)
- Validation: 15% (e.g., 15,000 candles)
- Test: 15% (e.g., 15,000 candles)

With 100,000 candles:
- Train set covers ~2 years
- Val set covers ~6 months
- Test set covers ~6 months (most recent)

## Data Collection Time Estimates

| Time Period | Candles | API Calls | Time | File Size |
|-------------|---------|-----------|------|-----------|
| 3 months    | 8,640   | 9         | 2 min | 1.3 MB |
| 6 months    | 17,280  | 18        | 4 min | 2.6 MB |
| 1 year      | 34,560  | 35        | 9 min | 5.2 MB |
| 2 years     | 69,120  | 70        | 18 min | 10.4 MB |
| 3 years     | 103,680 | 104       | 26 min | 15.6 MB |
| Since 2019  | 300,000+ | 300+     | 75 min | 45+ MB |

**Note**: Times are approximate. Actual time depends on:
- Your internet speed
- Binance API response time
- Rate limiting (0.25s between requests)

## How to Fetch Historical Data

### Option 1: Interactive Script (Recommended)

```batch
cd e:\haseeb\current_candle_bot
venv\Scripts\activate
python fetch_historical_data.py
```

You'll see a menu:
```
1. Last 6 months  (~17,280 candles, ~4 min)
2. Last 1 year    (~34,560 candles, ~9 min)
3. Last 2 years   (~69,120 candles, ~18 min)
4. Last 3 years   (~103,680 candles, ~26 min)
5. Since 2019     (~300,000+ candles, ~75 min)
6. Custom date

Select option (1-6):
```

### Option 2: Python Script

```python
from fetch_historical_data import BinanceDataFetcher

fetcher = BinanceDataFetcher(
    symbol="BTCUSDT",
    interval="15m",
    output_file="data/candles_15m.csv"
)

# Fetch last 2 years
fetcher.fetch_data(start_date="2023-01-01")
```

### Option 3: From Jupyter Notebook

Add this cell to the training notebook:

```python
from fetch_historical_data import BinanceDataFetcher
from datetime import datetime, timedelta

# Fetch last 2 years
start_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")

fetcher = BinanceDataFetcher()
result = fetcher.fetch_data(start_date=start_date)

print(f"Fetched {result['candles_fetched']:,} candles in {result['elapsed_seconds']:.0f} seconds")
```

## Data Quality Checks

After fetching, verify your data:

```python
import pandas as pd

df = pd.read_csv("data/candles_15m.csv")

print(f"Total candles: {len(df):,}")
print(f"Date range: {pd.to_datetime(df['open_time_ms'].min(), unit='ms')} to {pd.to_datetime(df['open_time_ms'].max(), unit='ms')}")
print(f"Missing values: {df.isnull().sum().sum()}")
print(f"Duplicate timestamps: {df['open_time_ms'].duplicated().sum()}")

# Check for gaps
df['time_diff'] = df['open_time_ms'].diff()
gaps = df[df['time_diff'] > 900000]  # 15 min = 900000 ms
print(f"Gaps detected: {len(gaps)}")
```

## Training Performance by Dataset Size

Based on typical LSTM training:

| Dataset Size | Training Time | Expected Accuracy | Regime Coverage |
|--------------|---------------|-------------------|-----------------|
| 10,000 candles | 5-10 min | 50-55% | Poor (limited regimes) |
| 30,000 candles | 15-20 min | 52-57% | Fair (some regimes) |
| 70,000 candles | 30-40 min | 54-60% | Good (most regimes) |
| 100,000+ candles | 45-60 min | 55-62% | Excellent (all regimes) |

**Recommendation**: Start with 1-2 years for initial training, then expand to 3+ years for production.

## Model Performance Expectations

### With 6 Months Data
- ✓ Fast to train (15 min)
- ✗ May overfit to recent market regime
- ✗ Poor generalization to different conditions
- **Use case**: Testing, experimentation

### With 1-2 Years Data
- ✓ Good balance of training time and performance
- ✓ Covers multiple market regimes
- ✓ Decent generalization
- **Use case**: Initial production deployment

### With 3+ Years Data
- ✓ Excellent regime coverage
- ✓ Best generalization
- ✓ More robust to market changes
- ✗ Longer training time (45-60 min)
- **Use case**: Production-ready model

## When to Retrain

Retrain your model when:
- **Every 1-3 months** (recommended)
- After major market regime changes
- When alert precision drops below 65%
- When new data accumulates (additional 10,000+ candles)

## Storage Considerations

### Disk Space Requirements
- **Raw candles CSV**: ~150 bytes per candle
  - 100,000 candles = ~15 MB
  - 1 million candles = ~150 MB

- **Feature store (Parquet)**: ~500 bytes per candle
  - 100,000 candles = ~50 MB

- **Models**: ~10-20 MB per trained model

**Total for 3 years**: ~100 MB (very manageable!)

## Memory Requirements

### During Training
- **Features in RAM**: Sequence length (64) × Features (27) × 4 bytes × Samples
  - 100,000 samples = ~700 MB

- **Model**: ~50 MB

- **PyTorch overhead**: ~200 MB

**Total RAM needed**: 2-4 GB (comfortable on any modern PC)

### During Inference (Live Bot)
- **Candle buffer**: 64 candles = ~50 KB
- **Model**: ~50 MB
- **Python overhead**: ~100 MB

**Total RAM needed**: 200-500 MB (very light!)

## FAQ

**Q: Can I start with less data?**
A: Yes, but expect lower accuracy. Minimum viable is 10,000 candles (~2 months).

**Q: Will more data always improve the model?**
A: Up to a point. Beyond 3-5 years, benefits plateau. Older data may be less relevant.

**Q: How often should I fetch new data?**
A: The bot automatically logs all live candles. Fetch historical data once, then let the bot accumulate new data.

**Q: What if the fetch fails?**
A: The script has retry logic. If it stops, just run it again with the same settings - it will continue from where it left off if you use `append=True`.

**Q: Can I fetch multiple pairs?**
A: Yes! Modify the script to loop through different symbols. But this bot is designed for BTCUSDT only.

**Q: Does fetching cost anything?**
A: No! Binance public API is free. No API key needed for historical data.

## Recommended Workflow

1. **First Time Setup** (Day 1):
   ```batch
   python fetch_historical_data.py
   # Choose option 4 (3 years) - Wait ~25 minutes
   ```

2. **Train Initial Model**:
   ```batch
   jupyter notebook
   # Open model_training.ipynb
   # Run all cells - Wait ~45 minutes
   ```

3. **Deploy Bot**:
   ```batch
   start_bot.bat
   # Bot starts accumulating live data
   ```

4. **Monthly Retraining**:
   - Bot has logged 2,880+ new candles (30 days)
   - Rerun training notebook
   - New data automatically included

---

**Bottom Line**: 
- **Minimum**: 6 months (~4 min fetch)
- **Recommended**: 2 years (~18 min fetch)
- **Optimal**: 3 years (~26 min fetch)

Start with 2 years for best balance of time and performance! 🚀
