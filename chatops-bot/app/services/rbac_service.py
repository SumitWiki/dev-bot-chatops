"""
Role-Based Access Control Service
Manages user permissions and access control for bot commands
"""
import logging
from typing import Optional, List
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

from app.config import RBAC_CONFIG, ROLE_PERMISSIONS

logger = logging.getLogger(__name__)


class RBACService:
    """Service for managing role-based access control"""
    
    def __init__(self):
        self.user_roles = RBAC_CONFIG
        self.role_permissions = ROLE_PERMISSIONS
    
    def get_user_role(self, user_id: int) -> Optional[str]:
        """Get the role of a user by their Telegram ID"""
        for role, user_ids in self.user_roles.items():
            if user_id in user_ids:
                return role
        return None
    
    def has_permission(self, user_id: int, permission: str) -> bool:
        """Check if a user has a specific permission"""
        role = self.get_user_role(user_id)
        if not role:
            logger.warning(f"User {user_id} has no assigned role")
            return False
        
        permissions = self.role_permissions.get(role, [])
        has_perm = permission in permissions
        
        if not has_perm:
            logger.warning(f"User {user_id} (role: {role}) denied permission: {permission}")
        
        return has_perm
    
    def get_user_permissions(self, user_id: int) -> List[str]:
        """Get all permissions for a user"""
        role = self.get_user_role(user_id)
        if not role:
            return []
        return self.role_permissions.get(role, [])
    
    def add_user_to_role(self, user_id: int, role: str) -> bool:
        """Add a user to a role (runtime only, not persistent)"""
        if role not in self.user_roles:
            return False
        
        if user_id not in self.user_roles[role]:
            self.user_roles[role].append(user_id)
            logger.info(f"Added user {user_id} to role {role}")
        return True
    
    def remove_user_from_role(self, user_id: int, role: str) -> bool:
        """Remove a user from a role (runtime only)"""
        if role not in self.user_roles:
            return False
        
        if user_id in self.user_roles[role]:
            self.user_roles[role].remove(user_id)
            logger.info(f"Removed user {user_id} from role {role}")
        return True
    
    def list_all_users(self) -> dict:
        """List all users and their roles"""
        return self.user_roles.copy()
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is an admin"""
        return self.get_user_role(user_id) == "admin"


# Create global instance
rbac = RBACService()


def require_permission(permission: str):
    """
    Decorator to require a specific permission for a command handler
    Usage: @require_permission("deploy")
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id
            username = update.effective_user.username or "Unknown"
            
            if not rbac.has_permission(user_id, permission):
                role = rbac.get_user_role(user_id)
                if role is None:
                    await update.message.reply_text(
                        "🚫 **Access Denied**\n\n"
                        "You are not authorized to use this bot.\n"
                        f"Your User ID: `{user_id}`\n\n"
                        "Please contact an administrator to get access.",
                        parse_mode="Markdown"
                    )
                else:
                    await update.message.reply_text(
                        f"🚫 **Permission Denied**\n\n"
                        f"Your role (`{role}`) doesn't have permission to use this command.\n"
                        f"Required permission: `{permission}`",
                        parse_mode="Markdown"
                    )
                logger.warning(f"Access denied for user {username} ({user_id}) - Permission: {permission}")
                return
            
            logger.info(f"User {username} ({user_id}) executing: {permission}")
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator


def admin_only(func):
    """Decorator to restrict command to admins only"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        if not rbac.is_admin(user_id):
            await update.message.reply_text(
                "🚫 **Admin Only**\n\n"
                "This command requires administrator privileges.",
                parse_mode="Markdown"
            )
            return
        
        return await func(update, context, *args, **kwargs)
    return wrapper
