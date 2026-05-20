"""
Feature Engineering Module
Converts OHLCV candles into ML-ready features
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class FeatureEngine:
    """
    Feature engineering for candlestick data.
    Builds features from OHLCV + volume pressure + volatility + patterns.
    """
    
    FEATURES_VERSION = "v3"
    
    def __init__(self, buffer_size: int = 64):
        """
        Initialize feature engine.
        
        Args:
            buffer_size: Number of candles to maintain for feature computation
        """
        self.buffer_size = buffer_size
        self.candle_buffer = []
        
    def add_candle(self, candle: Dict):
        """
        Add a candle to the buffer.
        
        Args:
            candle: Normalized candle dictionary
        """
        self.candle_buffer.append(candle)
        
        # Keep only the last buffer_size candles
        if len(self.candle_buffer) > self.buffer_size:
            self.candle_buffer.pop(0)
    
    def is_ready(self) -> bool:
        """Check if we have enough candles to compute features."""
        return len(self.candle_buffer) >= self.buffer_size
    
    def get_buffer_size(self) -> int:
        """Get current buffer size."""
        return len(self.candle_buffer)
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert candle buffer to pandas DataFrame."""
        return pd.DataFrame(self.candle_buffer)
    
    def compute_base_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute base OHLCV-derived features.
        
        Args:
            df: DataFrame with OHLCV columns
            
        Returns:
            DataFrame with added features
        """
        # Log return
        df['log_return'] = np.log(df['close'] / df['open'])
        
        # Range features
        df['range_pct'] = (df['high'] - df['low']) / df['close']
        df['body_pct'] = np.abs(df['close'] - df['open']) / df['close']
        
        # Wick features
        df['upper_wick'] = (df['high'] - df[['open', 'close']].max(axis=1)) / df['close']
        df['lower_wick'] = (df[['open', 'close']].min(axis=1) - df['low']) / df['close']
        
        # Close location value (CLV)
        df['clv'] = ((df['close'] - df['low']) - (df['high'] - df['close'])) / (df['high'] - df['low'] + 1e-10)
        df['clv'] = df['clv'].clip(-1, 1)
        
        # Directional volume
        df['direction'] = np.sign(df['close'] - df['open'])
        df['directional_volume'] = df['direction'] * df['volume']
        
        # Normalized volume (relative to SMA)
        for window in [5, 10, 20]:
            df[f'volume_sma_{window}'] = df['volume'].rolling(window).mean()
            df[f'volume_ratio_{window}'] = df['volume'] / (df[f'volume_sma_{window}'] + 1e-10)
        
        # Taker buy ratio (if available)
        if 'taker_buy_base_vol' in df.columns:
            df['taker_buy_ratio'] = df['taker_buy_base_vol'] / (df['volume'] + 1e-10)
        else:
            df['taker_buy_ratio'] = 0.5  # Neutral if not available
        
        return df
    
    def compute_volatility_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute volatility-based features.
        
        Args:
            df: DataFrame with price columns
            
        Returns:
            DataFrame with volatility features
        """
        # Rolling volatility of returns
        for window in [5, 10, 20]:
            df[f'volatility_{window}'] = df['log_return'].rolling(window).std()
        
        # ATR (Average True Range)
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift(1))
        low_close = np.abs(df['low'] - df['close'].shift(1))
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr_14'] = true_range.rolling(14).mean()
        df['atr_pct'] = df['atr_14'] / df['close']
        
        return df
    
    def compute_momentum_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute momentum indicators.
        
        Args:
            df: DataFrame with price columns
            
        Returns:
            DataFrame with momentum features
        """
        # EMA distances
        for window in [9, 21]:
            ema = df['close'].ewm(span=window, adjust=False).mean()
            df[f'ema_{window}_dist'] = (df['close'] - ema) / df['close']
        
        # RSI (Relative Strength Index)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 1e-10)
        df['rsi_14'] = 100 - (100 / (1 + rs))
        df['rsi_14_norm'] = (df['rsi_14'] - 50) / 50  # Normalize to [-1, 1]
        
        # Bollinger Bands
        sma_20 = df['close'].rolling(20).mean()
        std_20 = df['close'].rolling(20).std()
        df['bb_upper'] = sma_20 + 2 * std_20
        df['bb_lower'] = sma_20 - 2 * std_20
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'] + 1e-10)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / sma_20
        
        return df
    
    def compute_pattern_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute candlestick pattern features.
        
        Args:
            df: DataFrame with OHLCV columns
            
        Returns:
            DataFrame with pattern features
        """
        # Bullish/Bearish candle
        df['is_bullish'] = (df['close'] > df['open']).astype(int)
        df['is_bearish'] = (df['close'] < df['open']).astype(int)
        
        # Engulfing patterns
        df['bullish_engulfing'] = (
            (df['is_bullish'] == 1) &
            (df['is_bearish'].shift(1) == 1) &
            (df['open'] < df['close'].shift(1)) &
            (df['close'] > df['open'].shift(1))
        ).astype(int)
        
        df['bearish_engulfing'] = (
            (df['is_bearish'] == 1) &
            (df['is_bullish'].shift(1) == 1) &
            (df['open'] > df['close'].shift(1)) &
            (df['close'] < df['open'].shift(1))
        ).astype(int)
        
        # Pin bar (hammer/shooting star)
        body_size = np.abs(df['close'] - df['open'])
        total_range = df['high'] - df['low']
        
        df['bullish_pinbar'] = (
            (df['lower_wick'] > 2 * body_size) &
            (df['upper_wick'] < 0.5 * body_size) &
            (body_size / (total_range + 1e-10) < 0.3)
        ).astype(int)
        
        df['bearish_pinbar'] = (
            (df['upper_wick'] > 2 * body_size) &
            (df['lower_wick'] < 0.5 * body_size) &
            (body_size / (total_range + 1e-10) < 0.3)
        ).astype(int)
        
        # Inside bar
        df['inside_bar'] = (
            (df['high'] < df['high'].shift(1)) &
            (df['low'] > df['low'].shift(1))
        ).astype(int)
        
        return df
    
    def build_features(self) -> Optional[np.ndarray]:
        """
        Build complete feature set from candle buffer.
        
        Returns:
            NumPy array of shape (buffer_size, num_features) or None if not ready
        """
        if not self.is_ready():
            logger.warning(f"Not enough candles: {len(self.candle_buffer)}/{self.buffer_size}")
            return None
        
        try:
            # Convert to DataFrame
            df = self.to_dataframe()
            
            # Compute all feature groups
            df = self.compute_base_features(df)
            df = self.compute_volatility_features(df)
            df = self.compute_momentum_features(df)
            df = self.compute_pattern_features(df)
            
            # Select feature columns (exclude raw OHLCV and metadata)
            feature_cols = [
                'log_return', 'range_pct', 'body_pct', 'upper_wick', 'lower_wick',
                'clv', 'directional_volume', 'volume_ratio_5', 'volume_ratio_10', 'volume_ratio_20',
                'taker_buy_ratio', 'volatility_5', 'volatility_10', 'volatility_20',
                'atr_pct', 'ema_9_dist', 'ema_21_dist', 'rsi_14_norm',
                'bb_position', 'bb_width', 'is_bullish', 'is_bearish',
                'bullish_engulfing', 'bearish_engulfing', 'bullish_pinbar', 'bearish_pinbar',
                'inside_bar'
            ]
            
            # Handle missing features
            for col in feature_cols:
                if col not in df.columns:
                    df[col] = 0.0
            
            # Extract features
            features = df[feature_cols].values
            
            # Replace NaN/Inf with 0
            features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)
            
            return features.astype(np.float32)
            
        except Exception as e:
            logger.error(f"Error building features: {e}")
            return None
    
    def get_latest_candle_info(self) -> Dict:
        """
        Get information about the latest candle (for filtering).
        
        Returns:
            Dictionary with candle strength, volume, range info
        """
        if len(self.candle_buffer) == 0:
            return {}
        
        latest = self.candle_buffer[-1]
        close = latest['close']
        
        # Candle strength
        body_pct = abs(latest['close'] - latest['open']) / close
        range_pct = (latest['high'] - latest['low']) / close
        
        # Volume percentile (relative to buffer)
        volumes = [c['volume'] for c in self.candle_buffer]
        volume_pctile = sum(1 for v in volumes if v <= latest['volume']) / len(volumes) * 100
        
        return {
            'body_pct': body_pct,
            'range_pct': range_pct,
            'volume_pctile': volume_pctile,
            'is_bullish': latest['close'] > latest['open'],
            'is_bearish': latest['close'] < latest['open'],
            'close': close,
            'volume': latest['volume'],
        }


if __name__ == "__main__":
    # Test feature engine
    print("Testing FeatureEngine...")
    
    engine = FeatureEngine(buffer_size=64)
    
    # Generate dummy candles
    for i in range(70):
        candle = {
            'open_time_ms': i * 900000,
            'close_time_ms': (i + 1) * 900000,
            'open': 50000 + i * 10,
            'high': 50100 + i * 10,
            'low': 49900 + i * 10,
            'close': 50050 + i * 10,
            'volume': 100 + i,
            'taker_buy_base_vol': 50 + i * 0.5,
        }
        engine.add_candle(candle)
    
    print(f"Buffer size: {engine.get_buffer_size()}")
    print(f"Ready: {engine.is_ready()}")
    
    features = engine.build_features()
    if features is not None:
        print(f"Features shape: {features.shape}")
        print(f"Features dtype: {features.dtype}")
        print(f"Sample features (last candle): {features[-1][:5]}")
    
    info = engine.get_latest_candle_info()
    print(f"Latest candle info: {info}")
