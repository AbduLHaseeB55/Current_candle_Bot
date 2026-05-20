"""
Historical Data Fetcher for Binance BTCUSDT 15m Candles
Pulls data from official Binance Spot API and saves to data/candles_15m.csv
"""
import requests
import csv
import time
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BinanceDataFetcher:
    """Fetches historical kline data from Binance API."""
    
    BASE_URL = "https://api.binance.com/api/v3/klines"
    
    def __init__(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "15m",
        output_file: str = "data/candles_15m.csv"
    ):
        """
        Initialize data fetcher.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            interval: Timeframe (e.g., '15m')
            output_file: Path to output CSV file
        """
        self.symbol = symbol
        self.interval = interval
        self.output_file = Path(output_file)
        self.limit = 1000  # Max per API request
        
        # Create data directory if needed
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # CSV headers matching our bot's schema
        self.headers = [
            "symbol", "interval", "open_time_ms", "close_time_ms",
            "open", "high", "low", "close", "volume",
            "num_trades", "quote_volume",
            "taker_buy_base_vol", "taker_buy_quote_vol"
        ]
    
    def calculate_data_needs(self, start_date: str) -> dict:
        """
        Calculate how much data will be fetched and time estimates.
        
        Args:
            start_date: Start date in 'YYYY-MM-DD' format
            
        Returns:
            Dictionary with estimates
        """
        start_ts = datetime.strptime(start_date, "%Y-%m-%d")
        now = datetime.now()
        
        days_span = (now - start_ts).days
        
        # 15m = 96 candles per day
        candles_per_day = 96
        total_candles = days_span * candles_per_day
        
        # API calls needed (1000 candles per call)
        api_calls = (total_candles // self.limit) + 1
        
        # Time estimate (0.25s per call + safety margin)
        estimated_seconds = api_calls * 0.25 + 10
        estimated_minutes = estimated_seconds / 60
        
        # File size estimate (each row ~150 bytes)
        estimated_mb = (total_candles * 150) / (1024 * 1024)
        
        return {
            'start_date': start_date,
            'days_span': days_span,
            'total_candles': total_candles,
            'api_calls': api_calls,
            'estimated_time_seconds': estimated_seconds,
            'estimated_time_minutes': estimated_minutes,
            'estimated_file_size_mb': estimated_mb,
        }
    
    def fetch_data(self, start_date: str = "2019-01-01", append: bool = False):
        """
        Fetch historical data from Binance API.
        
        Args:
            start_date: Start date in 'YYYY-MM-DD' format
            append: If True, append to existing file; if False, overwrite
        """
        # Calculate estimates
        estimates = self.calculate_data_needs(start_date)
        
        logger.info("=" * 60)
        logger.info("BINANCE HISTORICAL DATA FETCHER")
        logger.info("=" * 60)
        logger.info(f"Symbol: {self.symbol}")
        logger.info(f"Interval: {self.interval}")
        logger.info(f"Start Date: {start_date}")
        logger.info(f"Output: {self.output_file}")
        logger.info(f"")
        logger.info(f"Estimated candles: {estimates['total_candles']:,}")
        logger.info(f"Estimated API calls: {estimates['api_calls']:,}")
        logger.info(f"Estimated time: {estimates['estimated_time_minutes']:.1f} minutes")
        logger.info(f"Estimated file size: {estimates['estimated_file_size_mb']:.1f} MB")
        logger.info("=" * 60)
        
        # Convert start date to timestamp
        start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp() * 1000)
        
        # Open file for writing
        mode = "a" if append and self.output_file.exists() else "w"
        write_header = mode == "w" or not self.output_file.exists()
        
        candles_fetched = 0
        api_calls_made = 0
        start_time = time.time()
        
        with open(self.output_file, mode, newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            
            # Write header if needed
            if write_header:
                writer.writerow(self.headers)
            
            # Fetch data in batches
            while True:
                params = {
                    "symbol": self.symbol,
                    "interval": self.interval,
                    "startTime": start_ts,
                    "limit": self.limit
                }
                
                try:
                    r = requests.get(self.BASE_URL, params=params, timeout=10)
                    r.raise_for_status()
                    data = r.json()
                    
                    api_calls_made += 1
                    
                    # Check if we got data
                    if not data:
                        break
                    
                    # Write candles to CSV
                    for k in data:
                        writer.writerow([
                            self.symbol,
                            self.interval,
                            k[0],           # open time
                            k[6],           # close time
                            float(k[1]),    # open
                            float(k[2]),    # high
                            float(k[3]),    # low
                            float(k[4]),    # close
                            float(k[5]),    # volume
                            int(k[8]),      # number of trades
                            float(k[7]),    # quote volume
                            float(k[9]),    # taker buy base volume
                            float(k[10])    # taker buy quote volume
                        ])
                        candles_fetched += 1
                    
                    # Update start timestamp for next batch
                    start_ts = data[-1][6] + 1
                    
                    # Progress update
                    current_date = datetime.fromtimestamp(start_ts / 1000)
                    elapsed = time.time() - start_time
                    
                    if api_calls_made % 10 == 0 or len(data) < self.limit:
                        logger.info(
                            f"Progress: {candles_fetched:,} candles | "
                            f"{api_calls_made} API calls | "
                            f"Up to: {current_date.strftime('%Y-%m-%d %H:%M')} | "
                            f"Elapsed: {elapsed:.1f}s"
                        )
                    
                    # Rate limiting safety (4 requests per second max)
                    time.sleep(0.25)
                    
                    # Stop if we've reached current time
                    if len(data) < self.limit:
                        break
                
                except requests.exceptions.RequestException as e:
                    logger.error(f"API request failed: {e}")
                    logger.info("Retrying in 5 seconds...")
                    time.sleep(5)
                    continue
        
        # Final summary
        elapsed_total = time.time() - start_time
        
        logger.info("=" * 60)
        logger.info("FETCH COMPLETE!")
        logger.info("=" * 60)
        logger.info(f"Total candles fetched: {candles_fetched:,}")
        logger.info(f"Total API calls: {api_calls_made}")
        logger.info(f"Total time: {elapsed_total:.1f} seconds ({elapsed_total/60:.1f} minutes)")
        logger.info(f"Output file: {self.output_file}")
        logger.info(f"File size: {self.output_file.stat().st_size / (1024*1024):.2f} MB")
        logger.info("=" * 60)
        
        return {
            'candles_fetched': candles_fetched,
            'api_calls': api_calls_made,
            'elapsed_seconds': elapsed_total,
            'output_file': str(self.output_file)
        }


def main():
    """Main entry point."""
    print("\n" + "=" * 60)
    print("BINANCE HISTORICAL DATA FETCHER")
    print("Fetches BTCUSDT 15m candles for model training")
    print("=" * 60)
    
    # User configuration
    print("\nConfiguration Options:")
    print("1. Last 6 months  (~17,280 candles, ~4 min)")
    print("2. Last 1 year    (~34,560 candles, ~9 min)")
    print("3. Last 2 years   (~69,120 candles, ~18 min)")
    print("4. Last 3 years   (~103,680 candles, ~26 min)")
    print("5. Since 2019     (~300,000+ candles, ~75 min)")
    print("6. Custom date")
    
    choice = input("\nSelect option (1-6): ").strip()
    
    # Calculate start date based on choice
    from datetime import timedelta
    now = datetime.now()
    
    if choice == "1":
        start_date = (now - timedelta(days=180)).strftime("%Y-%m-%d")
    elif choice == "2":
        start_date = (now - timedelta(days=365)).strftime("%Y-%m-%d")
    elif choice == "3":
        start_date = (now - timedelta(days=730)).strftime("%Y-%m-%d")
    elif choice == "4":
        start_date = (now - timedelta(days=1095)).strftime("%Y-%m-%d")
    elif choice == "5":
        start_date = "2019-01-01"
    elif choice == "6":
        start_date = input("Enter start date (YYYY-MM-DD): ").strip()
    else:
        print("Invalid choice. Using last 1 year.")
        start_date = (now - timedelta(days=365)).strftime("%Y-%m-%d")
    
    # Create fetcher
    fetcher = BinanceDataFetcher(
        symbol="BTCUSDT",
        interval="15m",
        output_file="data/candles_15m.csv"
    )
    
    # Show estimates
    estimates = fetcher.calculate_data_needs(start_date)
    print(f"\nThis will fetch approximately:")
    print(f"  • {estimates['total_candles']:,} candles")
    print(f"  • Taking ~{estimates['estimated_time_minutes']:.0f} minutes")
    print(f"  • Creating ~{estimates['estimated_file_size_mb']:.1f} MB file")
    
    confirm = input(f"\nProceed with fetch? (y/n): ").strip().lower()
    
    if confirm != 'y':
        print("Cancelled.")
        return
    
    # Fetch data
    print("\nStarting fetch...\n")
    result = fetcher.fetch_data(start_date=start_date, append=False)
    
    print(f"\n✅ Success! Data saved to: {result['output_file']}")
    print(f"\nYou can now run the training notebook to train your model!")


if __name__ == "__main__":
    main()
