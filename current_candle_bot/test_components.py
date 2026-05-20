"""
Test Script - Verify Bot Components
Run this to ensure all modules work correctly before deploying
"""
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all modules can be imported."""
    logger.info("Testing imports...")
    try:
        import numpy
        import pandas
        import torch
        import websockets
        from dotenv import load_dotenv
        from telegram import Bot
        
        from binance_stream import BinanceKlineStream
        from features import FeatureEngine
        from regime_detection import RegimeDetector
        from model_inference import ModelInference, CandleLSTM
        from decision_engine import DecisionEngine
        from telegram_notifier import TelegramNotifier
        from dataset_writer import DatasetWriter
        
        logger.info("✓ All imports successful")
        return True
    except Exception as e:
        logger.error(f"✗ Import failed: {e}")
        return False

def test_feature_engine():
    """Test feature engine with dummy data."""
    logger.info("\nTesting FeatureEngine...")
    try:
        from features import FeatureEngine
        import numpy as np
        
        engine = FeatureEngine(buffer_size=64)
        
        # Add dummy candles
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
        
        assert engine.is_ready(), "Engine should be ready after 70 candles"
        
        features = engine.build_features()
        assert features is not None, "Features should not be None"
        assert features.shape == (64, 27), f"Expected (64, 27), got {features.shape}"
        
        logger.info(f"✓ FeatureEngine working (shape: {features.shape})")
        return True
    except Exception as e:
        logger.error(f"✗ FeatureEngine failed: {e}")
        return False

def test_regime_detection():
    """Test regime detector with dummy data."""
    logger.info("\nTesting RegimeDetector...")
    try:
        from regime_detection import RegimeDetector
        import pandas as pd
        import numpy as np
        
        # Create dummy DataFrame
        np.random.seed(42)
        df = pd.DataFrame({
            'open': 50000 + np.cumsum(np.random.randn(100) * 100),
            'high': 50100 + np.cumsum(np.random.randn(100) * 100),
            'low': 49900 + np.cumsum(np.random.randn(100) * 100),
            'close': 50000 + np.cumsum(np.random.randn(100) * 100),
            'volume': 1000 + np.random.rand(100) * 500,
        })
        
        detector = RegimeDetector()
        regime, metrics = detector.detect_regime(df)
        
        assert regime is not None, "Regime should not be None"
        assert 'adx' in metrics, "Metrics should contain ADX"
        
        logger.info(f"✓ RegimeDetector working (regime: {regime.value})")
        return True
    except Exception as e:
        logger.error(f"✗ RegimeDetector failed: {e}")
        return False

def test_model_inference():
    """Test model inference (creates dummy model if needed)."""
    logger.info("\nTesting ModelInference...")
    try:
        from model_inference import ModelInference, create_dummy_model
        import numpy as np
        
        model_path = "models/current_candle_lstm.pt"
        
        # Create dummy model if it doesn't exist
        if not Path(model_path).exists():
            logger.info("  Creating dummy model...")
            Path("models").mkdir(exist_ok=True)
            create_dummy_model(model_path, input_size=27)
        
        inference = ModelInference(model_path, smooth_alpha=0.25)
        
        if not inference.load_model(input_size=27):
            raise Exception("Failed to load model")
        
        # Test prediction with dummy data
        dummy_features = np.random.randn(64, 27).astype(np.float32)
        result = inference.predict(dummy_features)
        
        assert result is not None, "Prediction result should not be None"
        prob_up, prob_up_smoothed = result
        assert 0 <= prob_up <= 1, f"prob_up should be in [0,1], got {prob_up}"
        assert 0 <= prob_up_smoothed <= 1, f"prob_up_smoothed should be in [0,1], got {prob_up_smoothed}"
        
        logger.info(f"✓ ModelInference working (prob_up: {prob_up:.4f})")
        return True
    except Exception as e:
        logger.error(f"✗ ModelInference failed: {e}")
        return False

def test_decision_engine():
    """Test decision engine."""
    logger.info("\nTesting DecisionEngine...")
    try:
        from decision_engine import DecisionEngine, Decision
        
        engine = DecisionEngine(
            bull_threshold=0.65,
            bear_threshold=0.65,
            min_body_pct=0.0010,
            min_range_pct=0.0012,
            min_vol_pctile=60,
            cooldown_minutes=10,
            hysteresis_margin=0.03,
        )
        
        # Test with strong signal
        candle_info = {
            'body_pct': 0.0015,
            'range_pct': 0.0020,
            'volume_pctile': 75.0,
        }
        
        decision, reason, details = engine.decide(
            prob_up=0.78,
            prob_up_smoothed=0.75,
            candle_info=candle_info,
            regime="TREND"
        )
        
        assert decision in [Decision.ALERT_BULL, Decision.ALERT_BEAR, Decision.NO_ALERT]
        
        logger.info(f"✓ DecisionEngine working (decision: {decision.value})")
        return True
    except Exception as e:
        logger.error(f"✗ DecisionEngine failed: {e}")
        return False

def test_dataset_writer():
    """Test dataset writer."""
    logger.info("\nTesting DatasetWriter...")
    try:
        from dataset_writer import DatasetWriter
        import shutil
        
        # Use test directory
        test_dir = Path("data_test")
        if test_dir.exists():
            shutil.rmtree(test_dir)
        
        writer = DatasetWriter(data_dir=str(test_dir), use_parquet=False)
        
        # Write test candle
        candle = {
            'symbol': 'BTCUSDT',
            'interval': '15m',
            'open_time_ms': 1000000,
            'close_time_ms': 1900000,
            'open': 50000,
            'high': 50100,
            'low': 49900,
            'close': 50050,
            'volume': 100,
            'is_closed': True,
        }
        writer.write_candle(candle, force_write=True)
        
        # Write test prediction
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
            'reason': 'test',
        }
        writer.write_prediction(prediction, force_write=True)
        
        # Check files exist
        assert (test_dir / "candles_15m.csv").exists(), "Candles file should exist"
        assert (test_dir / "predictions_log.csv").exists(), "Predictions file should exist"
        
        # Cleanup
        shutil.rmtree(test_dir)
        
        logger.info("✓ DatasetWriter working")
        return True
    except Exception as e:
        logger.error(f"✗ DatasetWriter failed: {e}")
        return False

def test_env_file():
    """Check if .env file is configured."""
    logger.info("\nChecking .env configuration...")
    try:
        from dotenv import load_dotenv
        import os
        
        if not Path(".env").exists():
            logger.warning("⚠ .env file not found - copy from .env.template")
            return False
        
        load_dotenv()
        
        required_vars = [
            'TELEGRAM_BOT_TOKEN',
            'TELEGRAM_CHAT_ID',
            'SYMBOL',
            'INTERVAL',
            'MODEL_PATH',
        ]
        
        missing = []
        for var in required_vars:
            value = os.getenv(var)
            if not value or value.startswith('your_'):
                missing.append(var)
        
        if missing:
            logger.warning(f"⚠ Missing or unconfigured: {', '.join(missing)}")
            return False
        
        logger.info("✓ .env file configured")
        return True
    except Exception as e:
        logger.error(f"✗ .env check failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("CURRENT CANDLE BOT - COMPONENT TESTS")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("FeatureEngine", test_feature_engine()))
    results.append(("RegimeDetector", test_regime_detection()))
    results.append(("ModelInference", test_model_inference()))
    results.append(("DecisionEngine", test_decision_engine()))
    results.append(("DatasetWriter", test_dataset_writer()))
    results.append(("Environment", test_env_file()))
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        symbol = "✓" if passed else "✗"
        print(f"{symbol} {name}: {status}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    
    print("=" * 60)
    print(f"Total: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n✓ All tests passed! Bot is ready to run.")
        print("  Next step: python run_bot.py")
    else:
        print("\n✗ Some tests failed. Please fix issues before running bot.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
