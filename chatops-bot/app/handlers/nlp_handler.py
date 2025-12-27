"""
NLP Handler - Natural Language Processing for DevOps queries
Allows users to interact with the bot using natural language
"""
import re
import logging
from typing import Optional, Tuple
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters, Application

from app.services.docker_service import DockerService
from app.services.rbac_service import rbac

logger = logging.getLogger(__name__)

# Initialize Docker service
docker_service = DockerService()


class NLPHandler:
    """Handle natural language queries for DevOps operations"""
    
    # Intent patterns with keywords
    INTENT_PATTERNS = {
        "list_containers": [
            r"(list|show|display|get|what).*(container|docker|service)s?",
            r"(what|which).*(container|docker|service)s?.*(running|active|up)",
            r"running containers?",
            r"all containers?",
            r"show me (all )?containers?"
        ],
        "container_status": [
            r"(status|state|info|information|details?).*(of|for|about)?\s*(\w+)",
            r"(how is|check|what's|whats).*(status|state|health).*(\w+)",
            r"(\w+).*(status|state|running\??)",
            r"is (\w+) (running|up|down|stopped|alive)"
        ],
        "container_logs": [
            r"(show|get|display|view|fetch).*logs?.*(of|for|from)?\s*(\w+)",
            r"logs?\s*(of|for|from)?\s*(\w+)",
            r"(\w+)\s*logs?"
        ],
        "container_stats": [
            r"(show|get|display|view).*(stats?|statistics|metrics|usage|resources?).*(of|for)?\s*(\w+)",
            r"(stats?|statistics|metrics|usage|resources?)\s*(of|for)?\s*(\w+)",
            r"(cpu|memory|ram).*(usage|stats?).*(\w+)",
            r"(\w+).*(cpu|memory|ram|stats?|metrics)"
        ],
        "health_check": [
            r"(health|healthcheck|check health)",
            r"(are|is).*(healthy|health)",
            r"run health ?check",
            r"check all containers?"
        ],
        "start_container": [
            r"(start|run|launch|boot|bring up)\s+(\w+)",
            r"(start|run|launch|boot).*(container)?\s*(\w+)"
        ],
        "stop_container": [
            r"(stop|halt|kill|shutdown|shut down|bring down)\s+(\w+)",
            r"(stop|halt|kill|shutdown).*(container)?\s*(\w+)"
        ],
        "restart_container": [
            r"(restart|reboot|reload|bounce)\s+(\w+)",
            r"(restart|reboot|reload).*(container)?\s*(\w+)"
        ],
        "deploy_container": [
            r"(deploy|create|spin up|launch).*(\w+/\w+:?\w*).*as\s+(\w+)",
            r"deploy\s+(\S+)\s+(\S+)"
        ],
        "help": [
            r"(help|commands?|what can you do|how to|usage)",
            r"(show|list|display).*(commands?|help|menu)",
            r"^help$"
        ]
    }
    
    # Common container-related words to filter out
    STOP_WORDS = {
        "the", "a", "an", "is", "are", "of", "for", "from", "to", "in", "on",
        "with", "container", "containers", "docker", "status", "logs", "log",
        "stats", "statistics", "show", "get", "display", "view", "check",
        "running", "stopped", "health", "healthy"
    }
    
    def __init__(self):
        self.docker_service = docker_service
    
    def parse_intent(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse the user's natural language query to determine intent
        Returns: (intent, container_name or None)
        """
        text = text.lower().strip()
        
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    # Try to extract container name from the match
                    container_name = self._extract_container_name(text, match)
                    return intent, container_name
        
        return None, None
    
    def _extract_container_name(self, text: str, match: re.Match) -> Optional[str]:
        """Extract container name from matched text"""
        groups = match.groups()
        
        # Look for potential container names in match groups
        for group in groups:
            if group and group.lower() not in self.STOP_WORDS:
                # Validate it could be a container name
                if re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_.-]*$', group):
                    return group
        
        # Fallback: try to find container name after key phrases
        text = text.lower()
        
        # Patterns to find container names after
        after_patterns = [
            r'of\s+(\w+)',
            r'for\s+(\w+)',
            r'from\s+(\w+)',
            r'about\s+(\w+)',
            r'container\s+(\w+)',
            r'named?\s+(\w+)'
        ]
        
        for pattern in after_patterns:
            m = re.search(pattern, text)
            if m and m.group(1) not in self.STOP_WORDS:
                return m.group(1)
        
        return None
    
    async def process_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process a natural language message"""
        text = update.message.text
        user_id = update.effective_user.id
        
        logger.info(f"NLP processing: '{text}' from user {user_id}")
        
        intent, container_name = self.parse_intent(text)
        
        if intent is None:
            await update.message.reply_text(
                "🤔 I didn't understand that. Here are some things you can say:\n\n"
                "• \"Show me all containers\"\n"
                "• \"What's the status of my-app?\"\n"
                "• \"Show logs for nginx\"\n"
                "• \"Check container stats for web-server\"\n"
                "• \"Run health check\"\n"
                "• \"Restart my-container\"\n\n"
                "Or use /help for all commands."
            )
            return
        
        # Process based on intent
        try:
            if intent == "list_containers":
                await self._handle_list_containers(update, user_id)
            
            elif intent == "container_status":
                await self._handle_container_status(update, user_id, container_name)
            
            elif intent == "container_logs":
                await self._handle_container_logs(update, user_id, container_name)
            
            elif intent == "container_stats":
                await self._handle_container_stats(update, user_id, container_name)
            
            elif intent == "health_check":
                await self._handle_health_check(update, user_id)
            
            elif intent == "start_container":
                await self._handle_start_container(update, user_id, container_name)
            
            elif intent == "stop_container":
                await self._handle_stop_container(update, user_id, container_name)
            
            elif intent == "restart_container":
                await self._handle_restart_container(update, user_id, container_name)
            
            elif intent == "help":
                await self._handle_help(update, user_id)
            
            else:
                await update.message.reply_text(
                    "🔧 I understood your intent but couldn't process it. "
                    "Please try using a command like /status <container_name>"
                )
                
        except Exception as e:
            logger.error(f"Error processing NLP intent: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def _handle_list_containers(self, update: Update, user_id: int):
        """Handle list containers intent"""
        if not rbac.has_permission(user_id, "list"):
            await update.message.reply_text("🚫 You don't have permission to list containers.")
            return
        
        containers = self.docker_service.list_containers()
        
        if not containers:
            await update.message.reply_text("📭 No containers found.")
            return
        
        message = "📦 **Here are your containers:**\n\n"
        for c in containers:
            emoji = "🟢" if c["status"] == "running" else "🔴"
            message += f"{emoji} **{c['name']}** - {c['status']}\n"
        
        await update.message.reply_text(message, parse_mode="Markdown")
    
    async def _handle_container_status(self, update: Update, user_id: int, container_name: Optional[str]):
        """Handle container status intent"""
        if not rbac.has_permission(user_id, "status"):
            await update.message.reply_text("🚫 You don't have permission to view status.")
            return
        
        if not container_name:
            await update.message.reply_text(
                "❓ Which container? Please specify the name.\n"
                "Example: \"What's the status of my-app?\""
            )
            return
        
        status = self.docker_service.get_container_status(container_name)
        
        if "error" in status:
            await update.message.reply_text(f"❌ {status['error']}")
            return
        
        emoji = "🟢" if status["status"] == "running" else "🔴"
        message = (
            f"{emoji} **{status['name']}**\n\n"
            f"Status: {status['status']}\n"
            f"Image: `{status['image']}`\n"
            f"CPU: {status['cpu_percent']}%\n"
            f"Memory: {status['memory_usage']['percent']}%\n"
            f"Health: {status['health']}"
        )
        
        await update.message.reply_text(message, parse_mode="Markdown")
    
    async def _handle_container_logs(self, update: Update, user_id: int, container_name: Optional[str]):
        """Handle container logs intent"""
        if not rbac.has_permission(user_id, "logs"):
            await update.message.reply_text("🚫 You don't have permission to view logs.")
            return
        
        if not container_name:
            await update.message.reply_text(
                "❓ Which container's logs? Please specify.\n"
                "Example: \"Show logs for nginx\""
            )
            return
        
        logs = self.docker_service.get_container_logs(container_name, 30)
        
        if len(logs) > 3500:
            logs = logs[-3500:]
            logs = "...(truncated)\n" + logs
        
        await update.message.reply_text(
            f"📜 **Logs for {container_name}:**\n\n```\n{logs}\n```",
            parse_mode="Markdown"
        )
    
    async def _handle_container_stats(self, update: Update, user_id: int, container_name: Optional[str]):
        """Handle container stats intent"""
        if not rbac.has_permission(user_id, "stats"):
            await update.message.reply_text("🚫 You don't have permission to view stats.")
            return
        
        if not container_name:
            await update.message.reply_text(
                "❓ Which container? Please specify.\n"
                "Example: \"Show stats for my-app\""
            )
            return
        
        stats = self.docker_service.get_container_stats(container_name)
        
        if "error" in stats:
            await update.message.reply_text(f"❌ {stats['error']}")
            return
        
        message = (
            f"📊 **Stats for {stats['name']}:**\n\n"
            f"🖥️ CPU: {stats['cpu_percent']}%\n"
            f"💾 Memory: {stats['memory']['used']} / {stats['memory']['limit']} ({stats['memory']['percent']}%)\n"
            f"🌐 Network: ⬇️{stats['network_io']['rx']} ⬆️{stats['network_io']['tx']}\n"
            f"💿 Disk: 📖{stats['block_io']['read']} ✏️{stats['block_io']['write']}"
        )
        
        await update.message.reply_text(message, parse_mode="Markdown")
    
    async def _handle_health_check(self, update: Update, user_id: int):
        """Handle health check intent"""
        if not rbac.has_permission(user_id, "health"):
            await update.message.reply_text("🚫 You don't have permission to run health checks.")
            return
        
        results = self.docker_service.health_check_all()
        
        if not results:
            await update.message.reply_text("📭 No containers to check.")
            return
        
        message = "🏥 **Health Check Results:**\n\n"
        for r in results:
            if r["health"] == "healthy":
                emoji = "✅"
            elif r["health"] == "unhealthy":
                emoji = "❌"
            elif r["status"] != "running":
                emoji = "⏹️"
            else:
                emoji = "⚠️"
            message += f"{emoji} {r['name']}: {r['health']}\n"
        
        await update.message.reply_text(message, parse_mode="Markdown")
    
    async def _handle_start_container(self, update: Update, user_id: int, container_name: Optional[str]):
        """Handle start container intent"""
        if not rbac.has_permission(user_id, "start"):
            await update.message.reply_text("🚫 You don't have permission to start containers.")
            return
        
        if not container_name:
            await update.message.reply_text("❓ Which container should I start?")
            return
        
        success, message = self.docker_service.start_container(container_name)
        await update.message.reply_text(message)
    
    async def _handle_stop_container(self, update: Update, user_id: int, container_name: Optional[str]):
        """Handle stop container intent"""
        if not rbac.has_permission(user_id, "stop"):
            await update.message.reply_text("🚫 You don't have permission to stop containers.")
            return
        
        if not container_name:
            await update.message.reply_text("❓ Which container should I stop?")
            return
        
        success, message = self.docker_service.stop_container(container_name)
        await update.message.reply_text(message)
    
    async def _handle_restart_container(self, update: Update, user_id: int, container_name: Optional[str]):
        """Handle restart container intent"""
        if not rbac.has_permission(user_id, "restart"):
            await update.message.reply_text("🚫 You don't have permission to restart containers.")
            return
        
        if not container_name:
            await update.message.reply_text("❓ Which container should I restart?")
            return
        
        success, message = self.docker_service.restart_container(container_name)
        await update.message.reply_text(message)
    
    async def _handle_help(self, update: Update, user_id: int):
        """Handle help intent"""
        await update.message.reply_text(
            "🤖 **ChatOps Bot - Natural Language Guide**\n\n"
            "You can ask me things like:\n\n"
            "📦 **Containers:**\n"
            "• \"Show me all containers\"\n"
            "• \"What containers are running?\"\n\n"
            "📊 **Status & Stats:**\n"
            "• \"What's the status of nginx?\"\n"
            "• \"Show stats for my-app\"\n"
            "• \"Is web-server running?\"\n\n"
            "📜 **Logs:**\n"
            "• \"Show logs for api-server\"\n"
            "• \"Get logs from database\"\n\n"
            "🏥 **Health:**\n"
            "• \"Run health check\"\n"
            "• \"Are my containers healthy?\"\n\n"
            "⚙️ **Actions:**\n"
            "• \"Restart nginx\"\n"
            "• \"Stop web-server\"\n"
            "• \"Start database\"\n\n"
            "Or use /help for command list!",
            parse_mode="Markdown"
        )


# Create global instance
nlp_handler = NLPHandler()


def register_nlp_handler(application: Application):
    """Register the NLP message handler"""
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            nlp_handler.process_message
        )
    )
    logger.info("NLP handler registered")
