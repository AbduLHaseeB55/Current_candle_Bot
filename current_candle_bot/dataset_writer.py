"""
Dataset Persistence Module
Handles storage of candles, predictions, and alerts
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DatasetWriter:
    """
    Writes data to CSV/Parquet files with de-duplication.
    Supports three required datasets: candles, predictions, alerts.
    """
    
    def __init__(self, data_dir: str = "data", use_parquet: bool = False):
        """
        Initialize dataset writer.
        
        Args:
            data_dir: Directory to store datasets
            use_parquet: Use Parquet format instead of CSV
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.use_parquet = use_parquet
        self.file_ext = ".parquet" if use_parquet else ".csv"
        
        # File paths
        self.candles_file = self.data_dir / f"candles_15m{self.file_ext}"
        self.predictions_file = self.data_dir / f"predictions_log{self.file_ext}"
        self.alerts_file = self.data_dir / f"alerts_log{self.file_ext}"
        self.features_file = self.data_dir / "features_15m.parquet"
        
        # In-memory buffers for batch writing
        self.candles_buffer = []
        self.predictions_buffer = []
        self.alerts_buffer = []
        
        self.buffer_size = 10  # Write every N records
        
        logger.info(f"DatasetWriter initialized: {self.data_dir}")
    
    def write_candle(self, candle: Dict, force_write: bool = False):
        """
        Write a closed candle to the candles dataset.
        
        Args:
            candle: Normalized candle dictionary
            force_write: Force immediate write (ignore buffer)
        """
        # Only write closed candles
        if not candle.get('is_closed', False):
            return
        
        record = {
            'symbol': candle['symbol'],
            'interval': candle['interval'],
            'open_time_ms': candle['open_time_ms'],
            'close_time_ms': candle['close_time_ms'],
            'open': candle['open'],
            'high': candle['high'],
            'low': candle['low'],
            'close': candle['close'],
            'volume': candle['volume'],
            'num_trades': candle.get('num_trades', 0),
            'quote_volume': candle.get('quote_volume', 0),
            'taker_buy_base_vol': candle.get('taker_buy_base_vol', 0),
            'taker_buy_quote_vol': candle.get('taker_buy_quote_vol', 0),
        }
        
        self.candles_buffer.append(record)
        
        if force_write or len(self.candles_buffer) >= self.buffer_size:
            self._flush_candles()
    
    def write_prediction(self, prediction: Dict, force_write: bool = False):
        """
        Write an inference prediction to the predictions log.
        
        Args:
            prediction: Prediction dictionary
            force_write: Force immediate write
        """
        record = {
            'timestamp_ms': prediction.get('timestamp_ms', int(datetime.now().timestamp() * 1000)),
            'symbol': prediction['symbol'],
            'interval': prediction['interval'],
            'candle_open_time_ms': prediction['candle_open_time_ms'],
            'candle_close_time_ms': prediction.get('candle_close_time_ms', 0),
            'regime': prediction['regime'],
            'prob_up': prediction['prob_up'],
            'prob_down': prediction.get('prob_down', 1 - prediction['prob_up']),
            'prob_up_smoothed': prediction['prob_up_smoothed'],
            'threshold_bull': prediction['threshold_bull'],
            'threshold_bear': prediction['threshold_bear'],
            'strength_body_pct': prediction.get('strength_body_pct', 0),
            'range_pct': prediction.get('range_pct', 0),
            'volume_pctile': prediction.get('volume_pctile', 0),
            'cooldown_active': prediction.get('cooldown_active', False),
            'filters_passed': prediction['filters_passed'],
            'decision': prediction['decision'],
            'reason': prediction['reason'],
        }
        
        self.predictions_buffer.append(record)
        
        if force_write or len(self.predictions_buffer) >= self.buffer_size:
            self._flush_predictions()
    
    def write_alert(self, alert: Dict, force_write: bool = False):
        """
        Write an alert to the alerts log.
        
        Args:
            alert: Alert dictionary
            force_write: Force immediate write
        """
        record = {
            'timestamp_ms': alert.get('timestamp_ms', int(datetime.now().timestamp() * 1000)),
            'symbol': alert['symbol'],
            'interval': alert['interval'],
            'candle_open_time_ms': alert['candle_open_time_ms'],
            'direction': alert['direction'],
            'confidence': alert['confidence'],
            'regime': alert['regime'],
            'message_text': alert.get('message_text', ''),
        }
        
        self.alerts_buffer.append(record)
        
        if force_write or len(self.alerts_buffer) >= self.buffer_size:
            self._flush_alerts()
    
    def _flush_candles(self):
        """Flush candles buffer to disk."""
        if not self.candles_buffer:
            return
        
        try:
            new_df = pd.DataFrame(self.candles_buffer)
            
            # Load existing data if file exists
            if self.candles_file.exists():
                if self.use_parquet:
                    existing_df = pd.read_parquet(self.candles_file)
                else:
                    existing_df = pd.read_csv(self.candles_file)
                
                # Concatenate and de-duplicate by open_time_ms
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                combined_df = combined_df.drop_duplicates(subset=['open_time_ms'], keep='last')
                combined_df = combined_df.sort_values('open_time_ms')
            else:
                combined_df = new_df
            
            # Save
            if self.use_parquet:
                combined_df.to_parquet(self.candles_file, index=False)
            else:
                combined_df.to_csv(self.candles_file, index=False)
            
            logger.info(f"Wrote {len(self.candles_buffer)} candles to {self.candles_file}")
            self.candles_buffer.clear()
            
        except Exception as e:
            logger.error(f"Error flushing candles: {e}")
    
    def _flush_predictions(self):
        """Flush predictions buffer to disk."""
        if not self.predictions_buffer:
            return
        
        try:
            new_df = pd.DataFrame(self.predictions_buffer)
            
            # Append to existing data
            if self.predictions_file.exists():
                if self.use_parquet:
                    existing_df = pd.read_parquet(self.predictions_file)
                else:
                    existing_df = pd.read_csv(self.predictions_file)
                
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            else:
                combined_df = new_df
            
            # Save
            if self.use_parquet:
                combined_df.to_parquet(self.predictions_file, index=False)
            else:
                combined_df.to_csv(self.predictions_file, index=False)
            
            logger.info(f"Wrote {len(self.predictions_buffer)} predictions to {self.predictions_file}")
            self.predictions_buffer.clear()
            
        except Exception as e:
            logger.error(f"Error flushing predictions: {e}")
    
    def _flush_alerts(self):
        """Flush alerts buffer to disk."""
        if not self.alerts_buffer:
            return
        
        try:
            new_df = pd.DataFrame(self.alerts_buffer)
            
            # Append to existing data
            if self.alerts_file.exists():
                if self.use_parquet:
                    existing_df = pd.read_parquet(self.alerts_file)
                else:
                    existing_df = pd.read_csv(self.alerts_file)
                
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            else:
                combined_df = new_df
            
            # Save
            if self.use_parquet:
                combined_df.to_parquet(self.alerts_file, index=False)
            else:
                combined_df.to_csv(self.alerts_file, index=False)
            
            logger.info(f"Wrote {len(self.alerts_buffer)} alerts to {self.alerts_file}")
            self.alerts_buffer.clear()
            
        except Exception as e:
            logger.error(f"Error flushing alerts: {e}")
    
    def flush_all(self):
        """Flush all buffers to disk."""
        self._flush_candles()
        self._flush_predictions()
        self._flush_alerts()
        logger.info("All buffers flushed")
    
    def get_dataset_stats(self) -> Dict:
        """Get statistics about stored datasets."""
        stats = {}
        
        # Candles
        if self.candles_file.exists():
            if self.use_parquet:
                df = pd.read_parquet(self.candles_file)
            else:
                df = pd.read_csv(self.candles_file)
            stats['candles_count'] = len(df)
            stats['candles_date_range'] = (
                pd.to_datetime(df['open_time_ms'], unit='ms').min(),
                pd.to_datetime(df['open_time_ms'], unit='ms').max(),
            )
        else:
            stats['candles_count'] = 0
        
        # Predictions
        if self.predictions_file.exists():
            if self.use_parquet:
                df = pd.read_parquet(self.predictions_file)
            else:
                df = pd.read_csv(self.predictions_file)
            stats['predictions_count'] = len(df)
        else:
            stats['predictions_count'] = 0
        
        # Alerts
        if self.alerts_file.exists():
            if self.use_parquet:
                df = pd.read_parquet(self.alerts_file)
            else:
                df = pd.read_csv(self.alerts_file)
            stats['alerts_count'] = len(df)
        else:
            stats['alerts_count'] = 0
        
        return stats


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Testing DatasetWriter...")
    
    writer = DatasetWriter(data_dir="data_test", use_parquet=False)
    
    # Test writing candles
    print("\nWriting test candles...")
    for i in range(5):
        candle = {
            'symbol': 'BTCUSDT',
            'interval': '15m',
            'open_time_ms': 1000000 + i * 900000,
            'close_time_ms': 1000000 + (i + 1) * 900000,
            'open': 50000 + i * 10,
            'high': 50100 + i * 10,
            'low': 49900 + i * 10,
            'close': 50050 + i * 10,
            'volume': 100 + i,
            'is_closed': True,
        }
        writer.write_candle(candle)
    
    writer.flush_all()
    
    # Test writing predictions
    print("\nWriting test predictions...")
    prediction = {
        'symbol': 'BTCUSDT',
        'interval': '15m',
        'candle_open_time_ms': 1000000,
        'regime': 'TREND',
        'prob_up': 0.75,
        'prob_up_smoothed': 0.72,
        'threshold_bull': 0.65,
        'threshold_bear': 0.65,
        'filters_passed': True,
        'decision': 'ALERT_BULL',
        'reason': 'passed_all_filters',
    }
    writer.write_prediction(prediction, force_write=True)
    
    # Test writing alerts
    print("\nWriting test alert...")
    alert = {
        'symbol': 'BTCUSDT',
        'interval': '15m',
        'candle_open_time_ms': 1000000,
        'direction': 'BULL',
        'confidence': 0.72,
        'regime': 'TREND',
    }
    writer.write_alert(alert, force_write=True)
    
    # Get stats
    print("\nDataset stats:")
    stats = writer.get_dataset_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
