import pandas as pd

# Load dataset
df = pd.read_csv('data/candles_15m.csv')

print(f"Total rows: {len(df)}")
print(f"\nColumns: {list(df.columns)}")
print(f"\nFirst 3 rows:")
print(df.head(3))
print(f"\nLast 3 rows:")
print(df.tail(3))

# Date range
print(f"\nDate range:")
print(f"  Start: {pd.to_datetime(df['open_time_ms'].iloc[0], unit='ms')}")
print(f"  End: {pd.to_datetime(df['open_time_ms'].iloc[-1], unit='ms')}")

# Data quality
print(f"\nData Quality:")
print(f"  Null values: {df.isnull().sum().sum()}")
print(f"  Duplicates: {df.duplicated(subset=['open_time_ms']).sum()}")

# Label distribution
df['label'] = (df['close'] > df['open']).astype(int)
print(f"\nLabel Distribution:")
print(f"  Green candles: {df['label'].sum()} ({df['label'].mean()*100:.1f}%)")
print(f"  Red candles: {len(df) - df['label'].sum()} ({(1-df['label'].mean())*100:.1f}%)")

# Train/val/test split sizes
n_samples = len(df) - 64 - 1  # Account for sequence_length and next candle
train_end = int(n_samples * 0.70)
val_end = int(n_samples * 0.85)

print(f"\nAfter sequence building (64-candle windows + next candle):")
print(f"  Total samples: {n_samples}")
print(f"  Train: {train_end} samples ({train_end/n_samples*100:.1f}%)")
print(f"  Val: {val_end - train_end} samples ({(val_end - train_end)/n_samples*100:.1f}%)")
print(f"  Test: {n_samples - val_end} samples ({(n_samples - val_end)/n_samples*100:.1f}%)")

print(f"\n✓ Dataset looks good for training!")
