"""
Telegram Notifier Module
Sends alerts and status messages via Telegram Bot API
"""
import asyncio
import logging
from typing import Optional
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """
    Sends trading alerts and status messages via Telegram.
    """
    
    def __init__(self, bot_token: str, chat_id: str):
        """
        Initialize Telegram notifier.
        
        Args:
            bot_token: Telegram bot token from BotFather
            chat_id: Chat ID to send messages to
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        # Initialize bot (timeout handled by request context)
        self.bot = Bot(token=bot_token)
        self._verified = False
    
    async def verify_connection(self) -> bool:
        """
        Verify bot token and chat ID are valid.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Test bot connection
            bot_info = await self.bot.get_me()
            logger.info(f"Connected to Telegram bot: @{bot_info.username}")
            
            # Test sending a message
            await self.send_message("✅ Bot connected and ready!")
            
            self._verified = True
            return True
            
        except TelegramError as e:
            logger.error(f"Failed to verify Telegram connection: {e}")
            self._verified = False
            return False
    
    async def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """
        Send a text message.
        
        Args:
            text: Message text
            parse_mode: Parse mode (HTML or Markdown)
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=parse_mode
            )
            return True
            
        except TelegramError as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    async def send_alert(
        self,
        direction: str,
        symbol: str,
        interval: str,
        confidence: float,
        regime: str,
        candle_info: dict,
        reason: str = ""
    ) -> bool:
        """
        Send a trading alert with formatted details.
        
        Args:
            direction: "BULL" or "BEAR"
            symbol: Trading pair (e.g., "BTCUSDT")
            interval: Timeframe (e.g., "15m")
            confidence: Model confidence (0-1)
            regime: Market regime
            candle_info: Dictionary with candle details
            reason: Optional reason/context
            
        Returns:
            True if sent successfully, False otherwise
        """
        # Emoji based on direction
        emoji = "🟢" if direction == "BULL" else "🔴"
        
        # Format timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Build message
        message = f"{emoji} <b>{direction} SIGNAL</b> {emoji}\n\n"
        message += f"📊 <b>Symbol:</b> {symbol}\n"
        message += f"⏰ <b>Timeframe:</b> {interval}\n"
        message += f"🎯 <b>Confidence:</b> {confidence:.1%}\n"
        message += f"🌐 <b>Regime:</b> {regime}\n\n"
        
        # Add candle details if available
        if candle_info:
            message += f"📈 <b>Candle Details:</b>\n"
            if 'close' in candle_info:
                message += f"  • Close: ${candle_info['close']:.2f}\n"
            if 'body_pct' in candle_info:
                message += f"  • Body: {candle_info['body_pct']:.2%}\n"
            if 'range_pct' in candle_info:
                message += f"  • Range: {candle_info['range_pct']:.2%}\n"
            if 'volume_pctile' in candle_info:
                message += f"  • Volume: {candle_info['volume_pctile']:.0f}th percentile\n"
        
        if reason:
            message += f"\n💡 <i>{reason}</i>\n"
        
        message += f"\n🕐 {timestamp}"
        
        return await self.send_message(message)
    
    async def send_status(self, status_info: dict) -> bool:
        """
        Send a status update message.
        
        Args:
            status_info: Dictionary with status information
            
        Returns:
            True if sent successfully, False otherwise
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = "📊 <b>Bot Status Update</b>\n\n"
        
        for key, value in status_info.items():
            message += f"• <b>{key}:</b> {value}\n"
        
        message += f"\n🕐 {timestamp}"
        
        return await self.send_message(message)
    
    async def send_error(self, error_msg: str) -> bool:
        """
        Send an error notification.
        
        Args:
            error_msg: Error message
            
        Returns:
            True if sent successfully, False otherwise
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"⚠️ <b>Bot Error</b>\n\n"
        message += f"{error_msg}\n\n"
        message += f"🕐 {timestamp}"
        
        return await self.send_message(message)
    
    async def send_heartbeat(self, candles_processed: int, alerts_sent: int) -> bool:
        """
        Send a heartbeat message to show bot is alive.
        
        Args:
            candles_processed: Number of candles processed
            alerts_sent: Number of alerts sent
            
        Returns:
            True if sent successfully, False otherwise
        """
        status_info = {
            "Status": "✅ Running",
            "Candles Processed": candles_processed,
            "Alerts Sent": alerts_sent,
        }
        
        return await self.send_status(status_info)


async def test_telegram():
    """Test Telegram notifier with sample messages."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env")
        return
    
    notifier = TelegramNotifier(bot_token, chat_id)
    
    # Verify connection
    print("Verifying Telegram connection...")
    if not await notifier.verify_connection():
        print("Failed to verify connection!")
        return
    
    print("Connection verified!")
    
    # Test alert
    print("Sending test alert...")
    await notifier.send_alert(
        direction="BULL",
        symbol="BTCUSDT",
        interval="15m",
        confidence=0.78,
        regime="TREND",
        candle_info={
            'close': 50234.56,
            'body_pct': 0.0015,
            'range_pct': 0.0021,
            'volume_pctile': 72.5,
        },
        reason="Strong bullish momentum with high volume support"
    )
    
    print("Test complete!")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(test_telegram())
