"""
Binance WebSocket Stream Handler
Handles both wrapped and flattened kline message formats
"""
import asyncio
import json
import logging
import time
from typing import Callable, Dict, Optional
import websockets

logger = logging.getLogger(__name__)


class BinanceKlineStream:
    """
    Binance WebSocket client for streaming kline/candlestick data.
    Handles connection, reconnection, and message normalization.
    """
    
    def __init__(self, symbol: str, interval: str, on_candle: Callable):
        """
        Initialize the Binance kline stream.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            interval: Kline interval (e.g., '15m')
            on_candle: Callback function to process candle data
        """
        self.symbol = symbol.lower()
        self.interval = interval
        self.on_candle = on_candle
        self.ws_url = f"wss://stream.binance.com:9443/ws/{self.symbol}@kline_{self.interval}"
        self.websocket = None
        self.running = False
        self.reconnect_delay = 5
        self.max_reconnect_delay = 60
        
    def normalize_candle(self, message: Dict) -> Optional[Dict]:
        """
        Normalize candle data from different message formats.
        
        Handles two formats:
        1. Wrapped: {"e": "kline", "k": {...}}
        2. Flattened: {"t": ..., "o": ..., ...}
        
        Returns:
            Normalized candle dict or None if invalid
        """
        try:
            # Check if message has the wrapped format
            if "k" in message and "e" in message:
                kline = message["k"]
                return {
                    "symbol": kline["s"],
                    "interval": kline["i"],
                    "open_time_ms": kline["t"],
                    "close_time_ms": kline["T"],
                    "open": float(kline["o"]),
                    "high": float(kline["h"]),
                    "low": float(kline["l"]),
                    "close": float(kline["c"]),
                    "volume": float(kline["v"]),
                    "is_closed": kline["x"],
                    "num_trades": kline["n"],
                    "quote_volume": float(kline["q"]),
                    "taker_buy_base_vol": float(kline["V"]),
                    "taker_buy_quote_vol": float(kline["Q"]),
                }
            
            # Check if message has flattened format
            elif "t" in message and "o" in message:
                return {
                    "symbol": message.get("s", self.symbol.upper()),
                    "interval": message.get("i", self.interval),
                    "open_time_ms": message["t"],
                    "close_time_ms": message.get("T", message["t"] + 900000),  # Default 15m
                    "open": float(message["o"]),
                    "high": float(message["h"]),
                    "low": float(message["l"]),
                    "close": float(message["c"]),
                    "volume": float(message["v"]),
                    "is_closed": message.get("x", False),
                    "num_trades": message.get("n", 0),
                    "quote_volume": float(message.get("q", 0)),
                    "taker_buy_base_vol": float(message.get("V", 0)),
                    "taker_buy_quote_vol": float(message.get("Q", 0)),
                }
            
            else:
                logger.warning(f"Unknown message format: {message}")
                return None
                
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error normalizing candle: {e}, message: {message}")
            return None
    
    async def connect(self):
        """Establish WebSocket connection."""
        try:
            self.websocket = await websockets.connect(self.ws_url)
            logger.info(f"Connected to Binance WebSocket: {self.ws_url}")
            self.reconnect_delay = 5  # Reset delay on successful connection
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Binance WebSocket: {e}")
            return False
    
    async def listen(self):
        """Listen for incoming messages and process them."""
        if not self.websocket:
            logger.error("WebSocket not connected. Call connect() first.")
            return
        
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    candle = self.normalize_candle(data)
                    
                    if candle:
                        # Call the callback with normalized candle data
                        await self.on_candle(candle)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse message: {e}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
        except Exception as e:
            logger.error(f"Error in listen loop: {e}")
    
    async def run(self):
        """Main run loop with automatic reconnection."""
        self.running = True
        
        while self.running:
            try:
                # Connect to WebSocket
                if await self.connect():
                    # Listen for messages
                    await self.listen()
                
                # If we get here, connection was closed
                if self.running:
                    logger.info(f"Reconnecting in {self.reconnect_delay} seconds...")
                    await asyncio.sleep(self.reconnect_delay)
                    
                    # Exponential backoff for reconnection
                    self.reconnect_delay = min(
                        self.reconnect_delay * 2,
                        self.max_reconnect_delay
                    )
                    
            except Exception as e:
                logger.error(f"Error in run loop: {e}")
                if self.running:
                    await asyncio.sleep(self.reconnect_delay)
    
    async def stop(self):
        """Stop the stream gracefully."""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            logger.info("WebSocket connection closed")


async def test_stream():
    """Test the Binance stream with a simple callback."""
    async def on_candle(candle: Dict):
        is_closed = "CLOSED" if candle["is_closed"] else "LIVE"
        print(f"[{is_closed}] {candle['symbol']} {candle['interval']} "
              f"O:{candle['open']:.2f} H:{candle['high']:.2f} "
              f"L:{candle['low']:.2f} C:{candle['close']:.2f} "
              f"V:{candle['volume']:.2f}")
    
    stream = BinanceKlineStream("BTCUSDT", "15m", on_candle)
    
    try:
        await stream.run()
    except KeyboardInterrupt:
        print("\nStopping stream...")
        await stream.stop()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Starting Binance WebSocket test...")
    print("Press Ctrl+C to stop")
    asyncio.run(test_stream())
