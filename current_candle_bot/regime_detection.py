"""
Regime Detection Module
Detects market regime (TREND vs CHOP, volatility level)
"""
import numpy as np
import pandas as pd
from typing import Dict, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RegimeType(Enum):
    """Market regime types."""
    TREND = "TREND"
    CHOP = "CHOP"
    HIGH_VOL_TREND = "HIGH_VOL_TREND"
    HIGH_VOL_CHOP = "HIGH_VOL_CHOP"
    UNKNOWN = "UNKNOWN"


class RegimeDetector:
    """
    Detects market regime based on volatility and trend strength.
    Uses ATR, ADX-like metrics, and price action.
    """
    
    def __init__(
        self,
        trend_threshold: float = 25.0,
        high_vol_threshold: float = 70.0,
        atr_lookback: int = 14,
        adx_lookback: int = 14
    ):
        """
        Initialize regime detector.
        
        Args:
            trend_threshold: ADX-like threshold for trend vs chop
            high_vol_threshold: Volatility percentile threshold
            atr_lookback: Lookback period for ATR
            adx_lookback: Lookback period for trend strength
        """
        self.trend_threshold = trend_threshold
        self.high_vol_threshold = high_vol_threshold
        self.atr_lookback = atr_lookback
        self.adx_lookback = adx_lookback
    
    def compute_atr(self, df: pd.DataFrame) -> pd.Series:
        """
        Compute Average True Range.
        
        Args:
            df: DataFrame with OHLC columns
            
        Returns:
            ATR series
        """
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift(1))
        low_close = np.abs(df['low'] - df['close'].shift(1))
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(self.atr_lookback).mean()
        
        return atr
    
    def compute_adx_like(self, df: pd.DataFrame) -> pd.Series:
        """
        Compute ADX-like trend strength indicator.
        
        Args:
            df: DataFrame with OHLC columns
            
        Returns:
            Trend strength series (0-100)
        """
        # Compute directional movement
        high_diff = df['high'].diff()
        low_diff = -df['low'].diff()
        
        plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
        minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
        
        # True range
        atr = self.compute_atr(df)
        
        # Directional indicators
        plus_di = 100 * plus_dm.rolling(self.adx_lookback).mean() / (atr + 1e-10)
        minus_di = 100 * minus_dm.rolling(self.adx_lookback).mean() / (atr + 1e-10)
        
        # DX (Directional Movement Index)
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
        
        # ADX (smoothed DX)
        adx = dx.rolling(self.adx_lookback).mean()
        
        return adx
    
    def compute_volatility_percentile(self, df: pd.DataFrame, lookback: int = 100) -> pd.Series:
        """
        Compute rolling volatility percentile.
        
        Args:
            df: DataFrame with price columns
            lookback: Lookback period for percentile calculation
            
        Returns:
            Volatility percentile series (0-100)
        """
        returns = df['close'].pct_change()
        volatility = returns.rolling(self.atr_lookback).std()
        
        # Compute percentile rank
        vol_pctile = volatility.rolling(lookback).apply(
            lambda x: pd.Series(x).rank(pct=True).iloc[-1] * 100 if len(x) > 0 else 50,
            raw=False
        )
        
        return vol_pctile
    
    def detect_regime(self, df: pd.DataFrame) -> Tuple[RegimeType, Dict]:
        """
        Detect current market regime.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Tuple of (regime_type, regime_metrics)
        """
        if len(df) < max(self.atr_lookback, self.adx_lookback, 20):
            return RegimeType.UNKNOWN, {}
        
        try:
            # Compute metrics
            adx = self.compute_adx_like(df)
            vol_pctile = self.compute_volatility_percentile(df)
            atr = self.compute_atr(df)
            atr_pct = (atr / df['close'] * 100)
            
            # Get latest values
            current_adx = adx.iloc[-1]
            current_vol_pctile = vol_pctile.iloc[-1]
            current_atr_pct = atr_pct.iloc[-1]
            
            # Determine trend vs chop
            is_trending = current_adx > self.trend_threshold
            is_high_vol = current_vol_pctile > self.high_vol_threshold
            
            # Classify regime
            if is_trending and is_high_vol:
                regime = RegimeType.HIGH_VOL_TREND
            elif is_trending and not is_high_vol:
                regime = RegimeType.TREND
            elif not is_trending and is_high_vol:
                regime = RegimeType.HIGH_VOL_CHOP
            else:
                regime = RegimeType.CHOP
            
            # Metrics
            metrics = {
                'adx': float(current_adx),
                'vol_pctile': float(current_vol_pctile),
                'atr_pct': float(current_atr_pct),
                'is_trending': bool(is_trending),
                'is_high_vol': bool(is_high_vol),
            }
            
            return regime, metrics
            
        except Exception as e:
            logger.error(f"Error detecting regime: {e}")
            return RegimeType.UNKNOWN, {}
    
    def get_regime_thresholds(self, regime: RegimeType, base_bull: float, base_bear: float) -> Tuple[float, float]:
        """
        Get regime-adjusted thresholds.
        
        Higher thresholds in choppy markets to reduce false signals.
        Lower thresholds in trending markets to capture more signals.
        
        Args:
            regime: Detected regime type
            base_bull: Base bullish threshold
            base_bear: Base bearish threshold
            
        Returns:
            Tuple of (adjusted_bull_threshold, adjusted_bear_threshold)
        """
        adjustments = {
            RegimeType.TREND: 1.0,  # No adjustment
            RegimeType.CHOP: 1.15,  # 15% higher threshold (more conservative)
            RegimeType.HIGH_VOL_TREND: 0.95,  # 5% lower (capture volatility)
            RegimeType.HIGH_VOL_CHOP: 1.20,  # 20% higher (very conservative)
            RegimeType.UNKNOWN: 1.10,  # 10% higher (conservative default)
        }
        
        factor = adjustments.get(regime, 1.1)
        
        return (
            min(base_bull * factor, 0.95),  # Cap at 0.95
            min(base_bear * factor, 0.95)
        )


class RegimeConfig:
    """Configuration for regime-specific thresholds."""
    
    DEFAULT_THRESHOLDS = {
        'TREND': {'bull': 0.65, 'bear': 0.65},
        'CHOP': {'bull': 0.75, 'bear': 0.75},
        'HIGH_VOL_TREND': {'bull': 0.62, 'bear': 0.62},
        'HIGH_VOL_CHOP': {'bull': 0.78, 'bear': 0.78},
        'UNKNOWN': {'bull': 0.70, 'bear': 0.70},
    }
    
    @classmethod
    def get_thresholds(cls, regime: RegimeType) -> Dict[str, float]:
        """Get thresholds for a given regime."""
        regime_key = regime.value if isinstance(regime, RegimeType) else str(regime)
        return cls.DEFAULT_THRESHOLDS.get(regime_key, cls.DEFAULT_THRESHOLDS['UNKNOWN'])
    
    @classmethod
    def load_from_file(cls, filepath: str) -> Dict:
        """Load regime thresholds from JSON file."""
        import json
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load thresholds from {filepath}: {e}")
            return cls.DEFAULT_THRESHOLDS
    
    @classmethod
    def save_to_file(cls, thresholds: Dict, filepath: str):
        """Save regime thresholds to JSON file."""
        import json
        try:
            with open(filepath, 'w') as f:
                json.dump(thresholds, f, indent=2)
            logger.info(f"Saved thresholds to {filepath}")
        except Exception as e:
            logger.error(f"Could not save thresholds to {filepath}: {e}")


if __name__ == "__main__":
    # Test regime detector
    print("Testing RegimeDetector...")
    
    # Generate dummy data
    np.random.seed(42)
    n_candles = 100
    
    df = pd.DataFrame({
        'open': 50000 + np.cumsum(np.random.randn(n_candles) * 100),
        'high': 50100 + np.cumsum(np.random.randn(n_candles) * 100),
        'low': 49900 + np.cumsum(np.random.randn(n_candles) * 100),
        'close': 50000 + np.cumsum(np.random.randn(n_candles) * 100),
        'volume': 1000 + np.random.rand(n_candles) * 500,
    })
    
    detector = RegimeDetector()
    regime, metrics = detector.detect_regime(df)
    
    print(f"Detected regime: {regime.value}")
    print(f"Metrics: {metrics}")
    
    # Get regime-adjusted thresholds
    base_bull, base_bear = 0.65, 0.65
    adj_bull, adj_bear = detector.get_regime_thresholds(regime, base_bull, base_bear)
    print(f"Adjusted thresholds: Bull={adj_bull:.3f}, Bear={adj_bear:.3f}")
    
    # Test RegimeConfig
    print("\nDefault thresholds:")
    for regime_type in RegimeType:
        thresholds = RegimeConfig.get_thresholds(regime_type)
        print(f"  {regime_type.value}: {thresholds}")
