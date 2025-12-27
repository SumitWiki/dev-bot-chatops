"""
ChatOps DevOps Bot - Main Entry Point
A Telegram bot for managing Docker containers with DevOps commands
"""
import logging
import asyncio
from telegram.ext import Application

from app.config import TELEGRAM_BOT_TOKEN, LOG_LEVEL, LOG_FILE
from app.handlers.command_handlers import register_command_handlers
from app.handlers.nlp_handler import register_nlp_handler
from app.services.notification_service import notification_service

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, LOG_LEVEL),
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Start the bot"""
    logger.info("Starting ChatOps DevOps Bot...")
    
    # Validate bot token
    if TELEGRAM_BOT_TOKEN == "your-bot-token-here":
        logger.error("Please set your TELEGRAM_BOT_TOKEN in environment variables or config.py")
        print("\n❌ ERROR: Telegram Bot Token not configured!")
        print("Please set the TELEGRAM_BOT_TOKEN environment variable.")
        print("Get your token from @BotFather on Telegram.\n")
        return
    
    try:
        # Create application
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Set bot instance for notifications
        notification_service.set_bot(application.bot)
        
        # Register handlers
        register_command_handlers(application)
        register_nlp_handler(application)
        
        logger.info("Bot handlers registered successfully")
        
        # Start the bot
        print("🤖 ChatOps Bot is running! Press Ctrl+C to stop.")
        application.run_polling(allowed_updates=["message", "callback_query"])
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise


if __name__ == "__main__":
    main()
