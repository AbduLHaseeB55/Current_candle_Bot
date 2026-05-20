"""
Current Candle Close Bot - Main Runner
Ties all components together for 24/7 operation
"""
import asyncio
import os
import sys
import signal
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict
from dotenv import load_dotenv

# Import bot components
from binance_stream import BinanceKlineStream
from features import FeatureEngine
from regime_detection import RegimeDetector, RegimeConfig, RegimeType
from model_inference import ModelInference
from decision_engine import DecisionEngine, Decision
from telegram_notifier import TelegramNotifier
from dataset_writer import DatasetWriter

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/inference.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class CurrentCandleBot:
    """
    Main bot orchestrator for current candle close prediction.
    """
    
    def __init__(self):
        """Initialize the bot with all components."""
        # Load environment variables
        load_dotenv()
        
        # Configuration
        self.symbol = os.getenv("SYMBOL", "BTCUSDT")
        self.interval = os.getenv("INTERVAL", "15m")
        self.model_path = os.getenv("MODEL_PATH", "models/current_candle_lstm.pt")
        self.thresholds_path = os.getenv("THRESHOLDS_PATH", "artifacts/thresholds.json")
        
        # Thresholds
        self.bull_threshold = float(os.getenv("BULL_THRESHOLD", "0.65"))
        self.bear_threshold = float(os.getenv("BEAR_THRESHOLD", "0.65"))
        
        # Filters
        self.min_body_pct = float(os.getenv("MIN_BODY_PCT", "0.0010"))
        self.min_range_pct = float(os.getenv("MIN_RANGE_PCT", "0.0012"))
        self.min_vol_pctile = float(os.getenv("MIN_VOL_PCTILE", "60"))
        self.cooldown_minutes = int(os.getenv("COOLDOWN_MINUTES", "10"))
        
        # Smoothing
        self.smooth_alpha = float(os.getenv("SMOOTH_ALPHA", "0.25"))
        self.hysteresis_margin = float(os.getenv("HYSTERESIS_MARGIN", "0.03"))
        
        # Buffer size
        self.buffer_size = int(os.getenv("BUFFER_SIZE", "64"))
        
        # Telegram
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        # Initialize components
        logger.info("Initializing bot components...")
        
        self.feature_engine = FeatureEngine(buffer_size=self.buffer_size)
        self.regime_detector = RegimeDetector()
        self.model_inference = ModelInference(
            model_path=self.model_path,
            smooth_alpha=self.smooth_alpha
        )
        self.decision_engine = DecisionEngine(
            bull_threshold=self.bull_threshold,
            bear_threshold=self.bear_threshold,
            min_body_pct=self.min_body_pct,
            min_range_pct=self.min_range_pct,
            min_vol_pctile=self.min_vol_pctile,
            cooldown_minutes=self.cooldown_minutes,
            hysteresis_margin=self.hysteresis_margin,
        )
        
        # Telegram notifier (optional)
        self.telegram_notifier = None
        if self.telegram_token and self.telegram_chat_id:
            self.telegram_notifier = TelegramNotifier(
                self.telegram_token,
                self.telegram_chat_id
            )
        
        # Dataset writer
        self.dataset_writer = DatasetWriter(data_dir="data", use_parquet=False)
        
        # Load regime thresholds if available
        self.regime_thresholds = RegimeConfig.load_from_file(self.thresholds_path)
        
        # Stats
        self.candles_processed = 0
        self.alerts_sent = 0
        self.start_time = datetime.now()
        
        # Binance stream
        self.stream = BinanceKlineStream(
            symbol=self.symbol,
            interval=self.interval,
            on_candle=self.on_candle
        )
        
        # Shutdown flag
        self.running = False
    
    async def initialize(self):
        """Initialize async components."""
        logger.info("=" * 60)
        logger.info("CURRENT CANDLE CLOSE BOT - STARTING")
        logger.info("=" * 60)
        logger.info(f"Symbol: {self.symbol}")
        logger.info(f"Interval: {self.interval}")
        logger.info(f"Model: {self.model_path}")
        logger.info(f"Bull Threshold: {self.bull_threshold}")
        logger.info(f"Bear Threshold: {self.bear_threshold}")
        logger.info(f"Buffer Size: {self.buffer_size}")
        logger.info("=" * 60)
        
        # Load model
        logger.info("Loading model...")
        if not self.model_inference.load_model(input_size=27):
            logger.error("Failed to load model!")
            return False
        
        model_info = self.model_inference.get_model_info()
        logger.info(f"Model loaded: {model_info}")
        
        # Verify Telegram (if configured)
        if self.telegram_notifier:
            logger.info("Verifying Telegram connection...")
            if await self.telegram_notifier.verify_connection():
                logger.info("Telegram connected successfully!")
            else:
                logger.warning("Telegram verification failed - alerts will not be sent!")
                self.telegram_notifier = None
        else:
            logger.warning("Telegram not configured - running without alerts!")
        
        return True
    
    async def on_candle(self, candle: Dict):
        """
        Callback for each candle update from Binance stream.
        
        Args:
            candle: Normalized candle dictionary
        """
        try:
            # Add candle to feature engine
            self.feature_engine.add_candle(candle)
            
            # Only process closed candles
            if not candle['is_closed']:
                return
            
            logger.info(f"Closed candle received: {candle['symbol']} O:{candle['open']:.2f} "
                       f"H:{candle['high']:.2f} L:{candle['low']:.2f} C:{candle['close']:.2f}")
            
            # Write candle to dataset
            self.dataset_writer.write_candle(candle)
            self.candles_processed += 1
            
            # Check if we have enough candles
            if not self.feature_engine.is_ready():
                logger.info(f"Warming up... {self.feature_engine.get_buffer_size()}/{self.buffer_size} candles")
                return
            
            # Build features
            features = self.feature_engine.build_features()
            if features is None:
                logger.error("Failed to build features!")
                return
            
            # Detect regime
            df = self.feature_engine.to_dataframe()
            regime, regime_metrics = self.regime_detector.detect_regime(df)
            logger.info(f"Regime: {regime.value}, Metrics: {regime_metrics}")
            
            # Run inference
            result = self.model_inference.predict(features)
            if result is None:
                logger.error("Inference failed!")
                return
            
            prob_up, prob_up_smoothed = result
            logger.info(f"Model output: P(UP)={prob_up:.4f}, P(UP_smoothed)={prob_up_smoothed:.4f}")
            
            # Get candle info for filtering
            candle_info = self.feature_engine.get_latest_candle_info()
            
            # Make decision
            decision, reason, details = self.decision_engine.decide(
                prob_up=prob_up,
                prob_up_smoothed=prob_up_smoothed,
                candle_info=candle_info,
                regime=regime.value,
                regime_thresholds=self.regime_thresholds,
                use_smoothed=True
            )
            
            logger.info(f"Decision: {decision.value}, Reason: {reason}")
            
            # Write prediction to log
            prediction_record = {
                'symbol': self.symbol,
                'interval': self.interval,
                'candle_open_time_ms': candle['open_time_ms'],
                'candle_close_time_ms': candle['close_time_ms'],
                'regime': regime.value,
                'prob_up': prob_up,
                'prob_up_smoothed': prob_up_smoothed,
                'threshold_bull': details.get('threshold_used', self.bull_threshold),
                'threshold_bear': details.get('threshold_used', self.bear_threshold),
                'strength_body_pct': candle_info.get('body_pct', 0),
                'range_pct': candle_info.get('range_pct', 0),
                'volume_pctile': candle_info.get('volume_pctile', 0),
                'filters_passed': decision != Decision.NO_ALERT,
                'decision': decision.value,
                'reason': reason,
            }
            self.dataset_writer.write_prediction(prediction_record)
            
            # Send alert if needed
            if decision != Decision.NO_ALERT:
                direction = "BULL" if decision == Decision.ALERT_BULL else "BEAR"
                
                # Write alert record
                alert_record = {
                    'symbol': self.symbol,
                    'interval': self.interval,
                    'candle_open_time_ms': candle['open_time_ms'],
                    'direction': direction,
                    'confidence': prob_up_smoothed,
                    'regime': regime.value,
                }
                self.dataset_writer.write_alert(alert_record, force_write=True)  # Force immediate write
                self.alerts_sent += 1
                
                # Send Telegram alert
                if self.telegram_notifier:
                    await self.telegram_notifier.send_alert(
                        direction=direction,
                        symbol=self.symbol,
                        interval=self.interval,
                        confidence=prob_up_smoothed,
                        regime=regime.value,
                        candle_info=candle_info,
                        reason=f"Filters: {', '.join(details.get('filters_passed', []))}"
                    )
                
                logger.info(f"ALERT SENT: {direction} @ {prob_up_smoothed:.1%}")
            
        except Exception as e:
            logger.error(f"Error processing candle: {e}", exc_info=True)
    
    async def send_heartbeat(self):
        """Send periodic heartbeat messages."""
        while self.running:
            await asyncio.sleep(3600)  # Every hour
            
            if self.telegram_notifier:
                uptime = datetime.now() - self.start_time
                await self.telegram_notifier.send_heartbeat(
                    candles_processed=self.candles_processed,
                    alerts_sent=self.alerts_sent
                )
    
    async def run(self):
        """Main run loop."""
        self.running = True
        
        # Initialize
        if not await self.initialize():
            logger.error("Initialization failed!")
            return
        
        logger.info("Starting main loop...")
        
        # Start heartbeat task
        heartbeat_task = asyncio.create_task(self.send_heartbeat())
        
        try:
            # Run the stream
            await self.stream.run()
            
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
        finally:
            self.running = False
            await self.shutdown()
    
    async def shutdown(self):
        """Graceful shutdown."""
        logger.info("Shutting down...")
        
        # Stop stream
        await self.stream.stop()
        
        # Flush datasets
        self.dataset_writer.flush_all()
        
        # Get stats
        stats = self.dataset_writer.get_dataset_stats()
        logger.info(f"Final stats: {stats}")
        
        logger.info("Shutdown complete")


def main():
    """Entry point."""
    # Create bot
    bot = CurrentCandleBot()
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        logger.info(f"Signal {sig} received, initiating shutdown...")
        bot.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run bot
    try:
        asyncio.run(bot.run())
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
