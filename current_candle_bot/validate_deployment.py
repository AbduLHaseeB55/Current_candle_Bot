"""
Pre-Deployment Validation Script
Run this to verify all requirements are met before going live
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import json

# Color codes for Windows CMD
GREEN = ''
RED = ''
YELLOW = ''
RESET = ''

try:
    import colorama
    colorama.init()
    GREEN = colorama.Fore.GREEN
    RED = colorama.Fore.RED
    YELLOW = colorama.Fore.YELLOW
    RESET = colorama.Style.RESET_ALL
except:
    pass

def check_mark(passed):
    return f"{GREEN}✓{RESET}" if passed else f"{RED}✗{RESET}"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def validate_environment():
    """Validate .env file and required variables."""
    print_section("1. Environment Configuration")
    
    load_dotenv()
    
    required_vars = {
        'TELEGRAM_BOT_TOKEN': 'Telegram Bot Token',
        'TELEGRAM_CHAT_ID': 'Telegram Chat ID',
        'SYMBOL': 'Trading Symbol',
        'INTERVAL': 'Timeframe Interval',
        'MODEL_PATH': 'Model File Path',
        'BULL_THRESHOLD': 'Bull Threshold',
        'BEAR_THRESHOLD': 'Bear Threshold',
        'MIN_BODY_PCT': 'Min Body Percentage',
        'MIN_RANGE_PCT': 'Min Range Percentage',
        'MIN_VOL_PCTILE': 'Min Volume Percentile',
        'COOLDOWN_MINUTES': 'Cooldown Minutes',
    }
    
    all_passed = True
    for var, desc in required_vars.items():
        value = os.getenv(var)
        passed = value is not None and value != ''
        all_passed = all_passed and passed
        
        status = check_mark(passed)
        display_value = value if passed else f"{RED}MISSING{RESET}"
        if var in ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID'] and passed:
            display_value = f"{value[:10]}..."
        
        print(f"{status} {desc:.<30} {display_value}")
    
    return all_passed

def validate_model_files():
    """Check model and threshold files exist."""
    print_section("2. Model & Artifacts")
    
    files_to_check = {
        'models/current_candle_lstm.pt': 'Trained LSTM Model',
        'artifacts/thresholds.json': 'Regime Thresholds',
    }
    
    all_passed = True
    for filepath, desc in files_to_check.items():
        path = Path(filepath)
        passed = path.exists()
        all_passed = all_passed and passed
        
        status = check_mark(passed)
        size = f"({path.stat().st_size / 1024:.1f} KB)" if passed else f"{RED}NOT FOUND{RESET}"
        
        print(f"{status} {desc:.<30} {size}")
    
    # Validate thresholds.json structure
    if Path('artifacts/thresholds.json').exists():
        try:
            with open('artifacts/thresholds.json', 'r') as f:
                thresholds = json.load(f)
            
            required_regimes = ['TREND', 'CHOP', 'HIGH_VOL_TREND', 'HIGH_VOL_CHOP']
            regimes_ok = all(regime in thresholds for regime in required_regimes)
            
            status = check_mark(regimes_ok)
            print(f"{status} {'Threshold regimes valid':.<30} {list(thresholds.keys())}")
        except:
            print(f"{RED}✗{RESET} {'Threshold JSON parse':.<30} {RED}INVALID{RESET}")
            all_passed = False
    
    return all_passed

def validate_datasets():
    """Check dataset files exist."""
    print_section("3. Dataset Files")
    
    datasets = {
        'data/candles_15m.csv': 'Raw Candle Store (REQUIRED)',
        'data/predictions_log.csv': 'Predictions Log (REQUIRED)',
        'data/alerts_log.csv': 'Alerts Log (REQUIRED)',
        'data/training_runs.jsonl': 'Training Metadata (OPTIONAL)',
    }
    
    all_passed = True
    for filepath, desc in datasets.items():
        path = Path(filepath)
        passed = path.exists()
        
        if 'REQUIRED' in desc and not passed:
            all_passed = False
        
        status = check_mark(passed)
        
        if passed:
            size = path.stat().st_size
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size/1024:.1f} KB"
            else:
                size_str = f"{size/(1024*1024):.1f} MB"
            info = f"{size_str}"
        else:
            info = f"{YELLOW}Will be created on first run{RESET}" if 'OPTIONAL' in desc else f"{RED}MISSING - Run init_datasets.bat{RESET}"
        
        print(f"{status} {desc:.<40} {info}")
    
    return all_passed

def validate_directories():
    """Check required directories exist."""
    print_section("4. Directory Structure")
    
    directories = ['data', 'logs', 'models', 'artifacts']
    
    all_passed = True
    for dirname in directories:
        path = Path(dirname)
        passed = path.exists() and path.is_dir()
        all_passed = all_passed and passed
        
        status = check_mark(passed)
        info = "EXISTS" if passed else f"{RED}MISSING - Will create{RESET}"
        
        print(f"{status} {dirname + '/':<30} {info}")
        
        # Create if missing
        if not passed:
            path.mkdir(parents=True, exist_ok=True)
            print(f"       Created: {dirname}/")
    
    return all_passed

def validate_dependencies():
    """Check Python dependencies."""
    print_section("5. Python Dependencies")
    
    dependencies = [
        ('torch', 'PyTorch'),
        ('numpy', 'NumPy'),
        ('pandas', 'Pandas'),
        ('websockets', 'WebSockets'),
        ('telegram', 'Telegram Bot'),  # Changed from python-telegram-bot to telegram
        ('dotenv', 'Python DotEnv'),
        ('ta', 'Technical Analysis'),
    ]
    
    all_passed = True
    for module, desc in dependencies:
        try:
            __import__(module.replace('-', '_'))
            passed = True
        except ImportError:
            passed = False
            all_passed = False
        
        status = check_mark(passed)
        info = "Installed" if passed else f"{RED}MISSING - pip install {module}{RESET}"
        
        print(f"{status} {desc:.<30} {info}")
    
    return all_passed

def validate_bot_modules():
    """Check bot components can be imported."""
    print_section("6. Bot Components")
    
    components = [
        ('binance_stream', 'Binance WebSocket Stream'),
        ('features', 'Feature Engine'),
        ('regime_detection', 'Regime Detector'),
        ('model_inference', 'Model Inference'),
        ('decision_engine', 'Decision Engine'),
        ('telegram_notifier', 'Telegram Notifier'),
        ('dataset_writer', 'Dataset Writer'),
    ]
    
    all_passed = True
    for module, desc in components:
        try:
            __import__(module)
            passed = True
        except Exception as e:
            passed = False
            all_passed = False
        
        status = check_mark(passed)
        info = "OK" if passed else f"{RED}IMPORT ERROR{RESET}"
        
        print(f"{status} {desc:.<30} {info}")
    
    return all_passed

def main():
    print("\n" + "="*60)
    print("  PRE-DEPLOYMENT VALIDATION")
    print("  Current Candle Close Bot")
    print("="*60)
    
    results = {}
    
    results['environment'] = validate_environment()
    results['model_files'] = validate_model_files()
    results['datasets'] = validate_datasets()
    results['directories'] = validate_directories()
    results['dependencies'] = validate_dependencies()
    results['bot_modules'] = validate_bot_modules()
    
    # Final summary
    print_section("VALIDATION SUMMARY")
    
    all_passed = all(results.values())
    
    for check, passed in results.items():
        status = check_mark(passed)
        print(f"{status} {check.replace('_', ' ').title():.<40} {'PASS' if passed else f'{RED}FAIL{RESET}'}")
    
    print("\n" + "="*60)
    if all_passed:
        print(f"{GREEN}✓ ALL CHECKS PASSED - Ready to deploy!{RESET}")
        print("="*60)
        print("\nNext steps:")
        print("  1. Run: quick_test.bat (5-minute test)")
        print("  2. If test passes, run: start_bot_background.bat")
        print("  3. Monitor: logs\\inference.log")
    else:
        print(f"{RED}✗ VALIDATION FAILED - Fix issues above{RESET}")
        print("="*60)
        print("\nCommon fixes:")
        print("  - Missing datasets: Run init_datasets.bat")
        print("  - Missing dependencies: pip install -r requirements.txt")
        print("  - Missing .env variables: Check .env file")
    
    print()
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
