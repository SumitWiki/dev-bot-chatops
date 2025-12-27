"""
Notification Service - Sends alerts and notifications via Telegram
"""
import logging
from datetime import datetime
from typing import Optional, List
from telegram import Bot
from telegram.error import TelegramError

from app.config import TELEGRAM_BOT_TOKEN, NOTIFICATION_CHAT_ID

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications and alerts"""
    
    def __init__(self, bot: Optional[Bot] = None):
        self.bot = bot
        self.notification_chat_id = NOTIFICATION_CHAT_ID
        self.notification_history: List[dict] = []
    
    def set_bot(self, bot: Bot):
        """Set the bot instance"""
        self.bot = bot
    
    async def send_notification(self, message: str, chat_id: Optional[str] = None, 
                                parse_mode: str = "Markdown") -> bool:
        """Send a notification message"""
        if not self.bot:
            logger.error("Bot not initialized for notifications")
            return False
        
        target_chat = chat_id or self.notification_chat_id
        if not target_chat:
            logger.warning("No notification chat ID configured")
            return False
        
        try:
            await self.bot.send_message(
                chat_id=target_chat,
                text=message,
                parse_mode=parse_mode
            )
            
            # Store in history
            self.notification_history.append({
                "timestamp": datetime.now().isoformat(),
                "message": message,
                "chat_id": target_chat
            })
            
            logger.info(f"Notification sent to {target_chat}")
            return True
            
        except TelegramError as e:
            logger.error(f"Failed to send notification: {e}")
            return False
    
    async def notify_deployment(self, container_name: str, image: str, 
                                status: str, user: str) -> bool:
        """Send deployment notification"""
        emoji = "✅" if status == "success" else "❌"
        
        message = (
            f"{emoji} **Deployment Notification**\n\n"
            f"📦 Container: `{container_name}`\n"
            f"🐳 Image: `{image}`\n"
            f"📊 Status: {status.upper()}\n"
            f"👤 Triggered by: {user}\n"
            f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        return await self.send_notification(message)
    
    async def notify_container_stopped(self, container_name: str, reason: str = "Manual") -> bool:
        """Send notification when container stops"""
        message = (
            f"⏹️ **Container Stopped**\n\n"
            f"📦 Container: `{container_name}`\n"
            f"📝 Reason: {reason}\n"
            f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        return await self.send_notification(message)
    
    async def notify_container_started(self, container_name: str, user: str) -> bool:
        """Send notification when container starts"""
        message = (
            f"▶️ **Container Started**\n\n"
            f"📦 Container: `{container_name}`\n"
            f"👤 Started by: {user}\n"
            f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        return await self.send_notification(message)
    
    async def notify_rollback(self, container_name: str, previous_image: str, 
                              status: str, user: str) -> bool:
        """Send rollback notification"""
        emoji = "🔄" if status == "success" else "❌"
        
        message = (
            f"{emoji} **Rollback Notification**\n\n"
            f"📦 Container: `{container_name}`\n"
            f"🐳 Rolled back to: `{previous_image}`\n"
            f"📊 Status: {status.upper()}\n"
            f"👤 Triggered by: {user}\n"
            f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        return await self.send_notification(message)
    
    async def notify_health_alert(self, container_name: str, health_status: str, 
                                  details: str = "") -> bool:
        """Send health alert notification"""
        emoji = "🔴" if health_status in ["unhealthy", "dead", "exited"] else "🟡"
        
        message = (
            f"{emoji} **Health Alert**\n\n"
            f"📦 Container: `{container_name}`\n"
            f"💊 Health Status: {health_status}\n"
            f"📝 Details: {details or 'N/A'}\n"
            f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        return await self.send_notification(message)
    
    async def notify_error(self, error_type: str, details: str, 
                           container_name: Optional[str] = None) -> bool:
        """Send error notification"""
        message = (
            f"🚨 **Error Alert**\n\n"
            f"⚠️ Type: {error_type}\n"
        )
        
        if container_name:
            message += f"📦 Container: `{container_name}`\n"
        
        message += (
            f"📝 Details: {details}\n"
            f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        return await self.send_notification(message)
    
    async def notify_resource_alert(self, container_name: str, resource_type: str, 
                                    current_value: float, threshold: float) -> bool:
        """Send resource usage alert"""
        message = (
            f"⚠️ **Resource Alert**\n\n"
            f"📦 Container: `{container_name}`\n"
            f"📊 Resource: {resource_type}\n"
            f"📈 Current: {current_value}%\n"
            f"🎯 Threshold: {threshold}%\n"
            f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        return await self.send_notification(message)
    
    def get_notification_history(self, limit: int = 10) -> List[dict]:
        """Get recent notification history"""
        return self.notification_history[-limit:]


# Create global instance
notification_service = NotificationService()
