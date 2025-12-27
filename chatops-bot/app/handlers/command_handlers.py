"""
Command Handlers - Telegram bot command handlers for DevOps operations
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, Application

from app.services.docker_service import DockerService
from app.services.rbac_service import require_permission, admin_only, rbac
from app.services.notification_service import notification_service
from app.config import MAX_LOG_LINES

logger = logging.getLogger(__name__)

# Initialize Docker service
docker_service = DockerService()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    user_id = user.id
    role = rbac.get_user_role(user_id)
    
    welcome_message = (
        f"👋 **Welcome to ChatOps DevOps Bot!**\n\n"
        f"Hello, {user.first_name}!\n\n"
        f"🆔 Your User ID: `{user_id}`\n"
        f"👤 Your Role: `{role or 'Not Assigned'}`\n\n"
    )
    
    if role:
        permissions = rbac.get_user_permissions(user_id)
        welcome_message += (
            f"✅ Your Permissions: {', '.join(permissions)}\n\n"
            f"📋 Available Commands:\n"
            f"/help - Show all commands\n"
            f"/list - List all containers\n"
            f"/status [name] - Container status\n"
            f"/logs [name] - View container logs\n"
            f"/stats [name] - Container statistics\n"
            f"/health - Health check all containers\n"
        )
        
        if "deploy" in permissions:
            welcome_message += (
                f"/deploy [image] [name] - Deploy container\n"
                f"/rollback [name] [image] - Rollback container\n"
            )
        
        if "restart" in permissions:
            welcome_message += (
                f"/start_container [name] - Start container\n"
                f"/stop [name] - Stop container\n"
                f"/restart [name] - Restart container\n"
            )
    else:
        welcome_message += (
            "⚠️ You don't have access yet.\n"
            "Please contact an administrator with your User ID."
        )
    
    await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    user_id = update.effective_user.id
    permissions = rbac.get_user_permissions(user_id)
    
    help_text = (
        "🤖 **ChatOps Bot Commands**\n\n"
        "📋 **General Commands:**\n"
        "`/start` - Welcome message\n"
        "`/help` - Show this help\n"
        "`/myid` - Show your user ID\n\n"
    )
    
    if "list" in permissions:
        help_text += (
            "📦 **Container Info:**\n"
            "`/list` - List all containers\n"
            "`/status <name>` - Container details\n"
            "`/logs <name> [lines]` - View logs\n"
            "`/stats <name>` - Resource usage\n"
            "`/health` - Health check all\n\n"
        )
    
    if "deploy" in permissions:
        help_text += (
            "🚀 **Deployment:**\n"
            "`/deploy <image> <name>` - Deploy new container\n"
            "`/rollback <name> <image>` - Rollback to image\n\n"
        )
    
    if "restart" in permissions:
        help_text += (
            "⚙️ **Container Control:**\n"
            "`/start_container <name>` - Start container\n"
            "`/stop <name>` - Stop container\n"
            "`/restart <name>` - Restart container\n\n"
        )
    
    if rbac.is_admin(user_id):
        help_text += (
            "👑 **Admin Commands:**\n"
            "`/adduser <user_id> <role>` - Add user\n"
            "`/removeuser <user_id> <role>` - Remove user\n"
            "`/listusers` - List all users\n"
        )
    
    help_text += (
        "\n💬 **Natural Language:**\n"
        "You can also ask questions like:\n"
        "• \"Show me container stats\"\n"
        "• \"What containers are running?\"\n"
        "• \"Check health of my-app\"\n"
    )
    
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /myid command - Show user's Telegram ID"""
    user = update.effective_user
    await update.message.reply_text(
        f"👤 **Your Information**\n\n"
        f"🆔 User ID: `{user.id}`\n"
        f"📛 Username: @{user.username or 'N/A'}\n"
        f"👤 Name: {user.first_name} {user.last_name or ''}\n"
        f"🎭 Role: `{rbac.get_user_role(user.id) or 'Not Assigned'}`",
        parse_mode="Markdown"
    )


@require_permission("list")
async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /list command - List all containers"""
    await update.message.reply_text("🔍 Fetching containers...")
    
    try:
        containers = docker_service.list_containers()
        
        if not containers:
            await update.message.reply_text("📭 No containers found.")
            return
        
        message = "📦 **Containers:**\n\n"
        
        for c in containers:
            status_emoji = "🟢" if c["status"] == "running" else "🔴" if c["status"] == "exited" else "🟡"
            message += (
                f"{status_emoji} **{c['name']}**\n"
                f"   ID: `{c['id']}`\n"
                f"   Image: `{c['image']}`\n"
                f"   Status: {c['status']}\n"
                f"   Ports: {c['ports']}\n\n"
            )
        
        # Add quick action buttons
        keyboard = []
        for c in containers[:5]:  # Limit to first 5
            keyboard.append([
                InlineKeyboardButton(f"📊 {c['name']}", callback_data=f"status_{c['name']}")
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        
        await update.message.reply_text(message, parse_mode="Markdown", reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Error listing containers: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


@require_permission("status")
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status <container_name> command"""
    if not context.args:
        await update.message.reply_text(
            "⚠️ Usage: `/status <container_name>`",
            parse_mode="Markdown"
        )
        return
    
    container_name = context.args[0]
    await update.message.reply_text(f"🔍 Checking status of `{container_name}`...", parse_mode="Markdown")
    
    try:
        status = docker_service.get_container_status(container_name)
        
        if "error" in status:
            await update.message.reply_text(f"❌ {status['error']}")
            return
        
        status_emoji = "🟢" if status["status"] == "running" else "🔴"
        
        message = (
            f"{status_emoji} **Container Status: {status['name']}**\n\n"
            f"🆔 ID: `{status['id']}`\n"
            f"🐳 Image: `{status['image']}`\n"
            f"📊 Status: {status['status']}\n"
            f"💊 Health: {status['health']}\n"
            f"🖥️ CPU: {status['cpu_percent']}%\n"
            f"💾 Memory: {status['memory_usage']['used']} / {status['memory_usage']['limit']} "
            f"({status['memory_usage']['percent']}%)\n"
            f"🔌 Ports: {status['ports']}\n"
            f"📅 Started: {status['started_at'][:19] if status['started_at'] else 'N/A'}"
        )
        
        # Add action buttons
        keyboard = [
            [
                InlineKeyboardButton("📜 Logs", callback_data=f"logs_{container_name}"),
                InlineKeyboardButton("📊 Stats", callback_data=f"stats_{container_name}")
            ],
            [
                InlineKeyboardButton("🔄 Restart", callback_data=f"restart_{container_name}"),
                InlineKeyboardButton("⏹️ Stop", callback_data=f"stop_{container_name}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(message, parse_mode="Markdown", reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


@require_permission("logs")
async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /logs <container_name> [lines] command"""
    if not context.args:
        await update.message.reply_text(
            "⚠️ Usage: `/logs <container_name> [lines]`\n"
            "Example: `/logs my-app 100`",
            parse_mode="Markdown"
        )
        return
    
    container_name = context.args[0]
    lines = int(context.args[1]) if len(context.args) > 1 else MAX_LOG_LINES
    
    await update.message.reply_text(f"📜 Fetching logs for `{container_name}`...", parse_mode="Markdown")
    
    try:
        logs = docker_service.get_container_logs(container_name, lines)
        
        # Truncate if too long for Telegram
        if len(logs) > 4000:
            logs = logs[-4000:]
            logs = "...(truncated)\n" + logs
        
        await update.message.reply_text(
            f"📜 **Logs: {container_name}** (last {lines} lines)\n\n```\n{logs}\n```",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


@require_permission("stats")
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats <container_name> command"""
    if not context.args:
        await update.message.reply_text(
            "⚠️ Usage: `/stats <container_name>`",
            parse_mode="Markdown"
        )
        return
    
    container_name = context.args[0]
    await update.message.reply_text(f"📊 Fetching stats for `{container_name}`...", parse_mode="Markdown")
    
    try:
        stats = docker_service.get_container_stats(container_name)
        
        if "error" in stats:
            await update.message.reply_text(f"❌ {stats['error']}")
            return
        
        message = (
            f"📊 **Container Stats: {stats['name']}**\n\n"
            f"🖥️ **CPU Usage:** {stats['cpu_percent']}%\n\n"
            f"💾 **Memory:**\n"
            f"   Used: {stats['memory']['used']}\n"
            f"   Limit: {stats['memory']['limit']}\n"
            f"   Usage: {stats['memory']['percent']}%\n\n"
            f"🌐 **Network I/O:**\n"
            f"   ⬇️ Received: {stats['network_io']['rx']}\n"
            f"   ⬆️ Transmitted: {stats['network_io']['tx']}\n\n"
            f"💿 **Block I/O:**\n"
            f"   📖 Read: {stats['block_io']['read']}\n"
            f"   ✏️ Write: {stats['block_io']['write']}"
        )
        
        await update.message.reply_text(message, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


@require_permission("health")
async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /health command - Check health of all containers"""
    await update.message.reply_text("🏥 Running health checks...")
    
    try:
        results = docker_service.health_check_all()
        
        if not results:
            await update.message.reply_text("📭 No running containers to check.")
            return
        
        message = "🏥 **Health Check Results:**\n\n"
        
        for r in results:
            if r["status"] == "running":
                if r["health"] == "healthy":
                    emoji = "✅"
                elif r["health"] == "unhealthy":
                    emoji = "❌"
                else:
                    emoji = "⚠️"
            else:
                emoji = "⏹️"
            
            message += (
                f"{emoji} **{r['name']}**\n"
                f"   Status: {r['status']}\n"
                f"   Health: {r['health']}\n\n"
            )
        
        await update.message.reply_text(message, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


@require_permission("deploy")
async def deploy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /deploy <image> <name> command"""
    if len(context.args) < 2:
        await update.message.reply_text(
            "⚠️ Usage: `/deploy <image> <container_name>`\n"
            "Example: `/deploy nginx:latest my-nginx`",
            parse_mode="Markdown"
        )
        return
    
    image = context.args[0]
    name = context.args[1]
    user = update.effective_user.username or update.effective_user.first_name
    
    await update.message.reply_text(
        f"🚀 Deploying `{image}` as `{name}`...\nThis may take a moment.",
        parse_mode="Markdown"
    )
    
    try:
        success, message = docker_service.deploy_container(image, name)
        await update.message.reply_text(message, parse_mode="Markdown")
        
        # Send notification
        status = "success" if success else "failed"
        await notification_service.notify_deployment(name, image, status, user)
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        await update.message.reply_text(f"❌ Deployment failed: {str(e)}")
        await notification_service.notify_deployment(name, image, "failed", user)


@require_permission("rollback")
async def rollback_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /rollback <container_name> <previous_image> command"""
    if len(context.args) < 2:
        await update.message.reply_text(
            "⚠️ Usage: `/rollback <container_name> <previous_image>`\n"
            "Example: `/rollback my-app my-app:v1.0`",
            parse_mode="Markdown"
        )
        return
    
    container_name = context.args[0]
    previous_image = context.args[1]
    user = update.effective_user.username or update.effective_user.first_name
    
    await update.message.reply_text(
        f"🔄 Rolling back `{container_name}` to `{previous_image}`...",
        parse_mode="Markdown"
    )
    
    try:
        success, message = docker_service.rollback_container(container_name, previous_image)
        await update.message.reply_text(message, parse_mode="Markdown")
        
        # Send notification
        status = "success" if success else "failed"
        await notification_service.notify_rollback(container_name, previous_image, status, user)
        
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        await update.message.reply_text(f"❌ Rollback failed: {str(e)}")


@require_permission("start")
async def start_container_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start_container <name> command"""
    if not context.args:
        await update.message.reply_text(
            "⚠️ Usage: `/start_container <container_name>`",
            parse_mode="Markdown"
        )
        return
    
    container_name = context.args[0]
    user = update.effective_user.username or update.effective_user.first_name
    
    try:
        success, message = docker_service.start_container(container_name)
        await update.message.reply_text(message)
        
        if success:
            await notification_service.notify_container_started(container_name, user)
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


@require_permission("stop")
async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stop <name> command"""
    if not context.args:
        await update.message.reply_text(
            "⚠️ Usage: `/stop <container_name>`",
            parse_mode="Markdown"
        )
        return
    
    container_name = context.args[0]
    user = update.effective_user.username or update.effective_user.first_name
    
    try:
        success, message = docker_service.stop_container(container_name)
        await update.message.reply_text(message)
        
        if success:
            await notification_service.notify_container_stopped(container_name, f"Stopped by {user}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


@require_permission("restart")
async def restart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /restart <name> command"""
    if not context.args:
        await update.message.reply_text(
            "⚠️ Usage: `/restart <container_name>`",
            parse_mode="Markdown"
        )
        return
    
    container_name = context.args[0]
    
    try:
        success, message = docker_service.restart_container(container_name)
        await update.message.reply_text(message)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


# Admin Commands
@admin_only
async def adduser_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /adduser <user_id> <role> command"""
    if len(context.args) < 2:
        await update.message.reply_text(
            "⚠️ Usage: `/adduser <user_id> <role>`\n"
            "Roles: `admin`, `developer`, `viewer`",
            parse_mode="Markdown"
        )
        return
    
    try:
        user_id = int(context.args[0])
        role = context.args[1].lower()
        
        if rbac.add_user_to_role(user_id, role):
            await update.message.reply_text(
                f"✅ User `{user_id}` added to role `{role}`",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(f"❌ Invalid role: {role}")
            
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID. Must be a number.")


@admin_only
async def removeuser_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /removeuser <user_id> <role> command"""
    if len(context.args) < 2:
        await update.message.reply_text(
            "⚠️ Usage: `/removeuser <user_id> <role>`",
            parse_mode="Markdown"
        )
        return
    
    try:
        user_id = int(context.args[0])
        role = context.args[1].lower()
        
        if rbac.remove_user_from_role(user_id, role):
            await update.message.reply_text(
                f"✅ User `{user_id}` removed from role `{role}`",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(f"❌ Invalid role: {role}")
            
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID. Must be a number.")


@admin_only
async def listusers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /listusers command"""
    users = rbac.list_all_users()
    
    message = "👥 **User Roles:**\n\n"
    
    for role, user_ids in users.items():
        message += f"**{role.upper()}:**\n"
        if user_ids:
            for uid in user_ids:
                message += f"  • `{uid}`\n"
        else:
            message += "  • (none)\n"
        message += "\n"
    
    await update.message.reply_text(message, parse_mode="Markdown")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button callbacks"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    try:
        action, container_name = data.split("_", 1)
        
        if action == "status":
            if not rbac.has_permission(user_id, "status"):
                await query.message.reply_text("🚫 Permission denied")
                return
            status = docker_service.get_container_status(container_name)
            if "error" not in status:
                status_emoji = "🟢" if status["status"] == "running" else "🔴"
                await query.message.reply_text(
                    f"{status_emoji} **{status['name']}**: {status['status']}\n"
                    f"CPU: {status['cpu_percent']}% | Memory: {status['memory_usage']['percent']}%",
                    parse_mode="Markdown"
                )
        
        elif action == "logs":
            if not rbac.has_permission(user_id, "logs"):
                await query.message.reply_text("🚫 Permission denied")
                return
            logs = docker_service.get_container_logs(container_name, 20)
            if len(logs) > 4000:
                logs = logs[-4000:]
            await query.message.reply_text(f"```\n{logs}\n```", parse_mode="Markdown")
        
        elif action == "stats":
            if not rbac.has_permission(user_id, "stats"):
                await query.message.reply_text("🚫 Permission denied")
                return
            stats = docker_service.get_container_stats(container_name)
            if "error" not in stats:
                await query.message.reply_text(
                    f"📊 **{container_name}**\n"
                    f"CPU: {stats['cpu_percent']}%\n"
                    f"Memory: {stats['memory']['percent']}%",
                    parse_mode="Markdown"
                )
        
        elif action == "restart":
            if not rbac.has_permission(user_id, "restart"):
                await query.message.reply_text("🚫 Permission denied")
                return
            success, message = docker_service.restart_container(container_name)
            await query.message.reply_text(message)
        
        elif action == "stop":
            if not rbac.has_permission(user_id, "stop"):
                await query.message.reply_text("🚫 Permission denied")
                return
            success, message = docker_service.stop_container(container_name)
            await query.message.reply_text(message)
            
    except Exception as e:
        logger.error(f"Button callback error: {e}")
        await query.message.reply_text(f"❌ Error: {str(e)}")


def register_command_handlers(application: Application):
    """Register all command handlers with the application"""
    
    # General commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("myid", myid_command))
    
    # Container info commands
    application.add_handler(CommandHandler("list", list_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("logs", logs_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("health", health_command))
    
    # Container control commands
    application.add_handler(CommandHandler("deploy", deploy_command))
    application.add_handler(CommandHandler("rollback", rollback_command))
    application.add_handler(CommandHandler("start_container", start_container_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("restart", restart_command))
    
    # Admin commands
    application.add_handler(CommandHandler("adduser", adduser_command))
    application.add_handler(CommandHandler("removeuser", removeuser_command))
    application.add_handler(CommandHandler("listusers", listusers_command))
    
    # Callback query handler for inline buttons
    application.add_handler(CallbackQueryHandler(button_callback))
    
    logger.info("Command handlers registered successfully")
