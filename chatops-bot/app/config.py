"""
Configuration settings for ChatOps Bot
"""
import os
from typing import Dict, List

# Telegram Bot Token (Get from @BotFather on Telegram)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "your-bot-token-here")

# Role-Based Access Control Configuration
# Define user roles and their Telegram user IDs
RBAC_CONFIG: Dict[str, List[int]] = {
    "admin": [
        5049509051,  # Sumit Ranjan Jha - Admin
    ],
    "developer": [
        # Add developer Telegram user IDs here
    ],
    "viewer": [
        873534271,  # Viewer user
    ]
}

# Permission mappings for each role
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "admin": ["deploy", "rollback", "status", "logs", "restart", "stop", "start", "stats", "list", "health"],
    "developer": ["deploy", "rollback", "status", "logs", "stats", "list", "health"],
    "viewer": ["status", "logs", "stats", "list", "health"]
}

# Docker configuration
DOCKER_HOST = os.getenv("DOCKER_HOST", "unix:///var/run/docker.sock")

# Notification settings
NOTIFICATION_CHAT_ID = os.getenv("NOTIFICATION_CHAT_ID", "")  # Chat ID for alerts

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/chatops.log")

# Health check interval (seconds)
HEALTH_CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", "60"))

# Maximum log lines to return
MAX_LOG_LINES = int(os.getenv("MAX_LOG_LINES", "50"))

# Allowed registries for deployment
ALLOWED_REGISTRIES = [
    "docker.io",
    "ghcr.io",
    "registry.hub.docker.com"
]
