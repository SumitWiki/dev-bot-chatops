# 🤖 ChatOps DevOps Bot

A **Telegram bot** for managing Docker containers through chat commands and natural language. Perfect for DevOps automation, monitoring, and team collaboration.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Docker](https://img.shields.io/badge/Docker-Enabled-blue)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue)

## 🌟 Features

### 📋 Container Management
- **List** all Docker containers with status
- **Deploy** new containers from images
- **Start/Stop/Restart** containers
- **Rollback** to previous image versions
- **View logs** in real-time

### 📊 Monitoring & Stats
- CPU, Memory, Network, Disk I/O statistics
- Health checks for all containers
- Real-time status updates

### 🔒 Role-Based Access Control (RBAC)
- **Admin**: Full access to all commands
- **Developer**: Deploy, rollback, view status/logs
- **Viewer**: Read-only access to status and logs

### 💬 Natural Language Support
Ask questions naturally:
- "Show me all containers"
- "What's the status of nginx?"
- "Restart my-app"
- "Show logs for web-server"

### 🚨 Notifications
- Deployment success/failure alerts
- Container health alerts
- Start/stop notifications

---

## 🏗️ Project Structure

```
chatops-bot/
├── app/
│   ├── __init__.py
│   ├── config.py                 # Configuration settings
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── command_handlers.py   # Telegram command handlers
│   │   └── nlp_handler.py        # Natural language processing
│   └── services/
│       ├── __init__.py
│       ├── docker_service.py     # Docker API integration
│       ├── rbac_service.py       # Role-based access control
│       └── notification_service.py
├── logs/
│   └── .gitkeep
├── main.py                       # Application entry point
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Docker installed and running
- Telegram Bot Token (from @BotFather)

### Step 1: Create Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the prompts
3. Copy the **Bot Token** provided

### Step 2: Get Your Telegram User ID

1. Search for **@userinfobot** on Telegram
2. Start chat and it will show your User ID
3. Note this ID for admin access

### Step 3: Configure the Bot

```bash
cd chatops-bot

# Copy environment template
cp .env.example .env

# Edit .env file with your token
nano .env
```

Add your token:
```env
TELEGRAM_BOT_TOKEN=your-actual-bot-token-here
NOTIFICATION_CHAT_ID=your-chat-id-for-alerts
```

### Step 4: Add Admin User

Edit `app/config.py` and add your Telegram User ID:

```python
RBAC_CONFIG = {
    "admin": [
        123456789,  # Replace with your User ID
    ],
    "developer": [],
    "viewer": []
}
```

### Step 5: Run the Bot

#### Option A: Run with Docker (Recommended)
```bash
docker-compose up -d --build
```

#### Option B: Run Locally
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run the bot
python main.py
```

---

## 📱 Bot Commands

### General Commands
| Command | Description |
|---------|-------------|
| `/start` | Welcome message and user info |
| `/help` | Show all available commands |
| `/myid` | Display your Telegram User ID |

### Container Information
| Command | Description |
|---------|-------------|
| `/list` | List all containers |
| `/status <name>` | Get container details |
| `/logs <name> [lines]` | View container logs |
| `/stats <name>` | Container resource usage |
| `/health` | Health check all containers |

### Container Control
| Command | Description |
|---------|-------------|
| `/deploy <image> <name>` | Deploy new container |
| `/rollback <name> <image>` | Rollback to previous image |
| `/start_container <name>` | Start a container |
| `/stop <name>` | Stop a container |
| `/restart <name>` | Restart a container |

### Admin Commands
| Command | Description |
|---------|-------------|
| `/adduser <id> <role>` | Add user to role |
| `/removeuser <id> <role>` | Remove user from role |
| `/listusers` | List all users and roles |

---

## 💬 Natural Language Examples

The bot understands natural language queries:

```
📦 Containers:
• "Show me all containers"
• "What containers are running?"
• "List docker services"

📊 Status & Stats:
• "What's the status of nginx?"
• "Show stats for my-app"
• "Is web-server running?"
• "Check my-container health"

📜 Logs:
• "Show logs for api-server"
• "Get logs from database"
• "nginx logs please"

⚙️ Actions:
• "Restart nginx"
• "Stop web-server"
• "Start database"

🏥 Health:
• "Run health check"
• "Are my containers healthy?"
```

---

## 🔒 Role-Based Access Control

### Roles and Permissions

| Permission | Admin | Developer | Viewer |
|------------|:-----:|:---------:|:------:|
| list | ✅ | ✅ | ✅ |
| status | ✅ | ✅ | ✅ |
| logs | ✅ | ✅ | ✅ |
| stats | ✅ | ✅ | ✅ |
| health | ✅ | ✅ | ✅ |
| deploy | ✅ | ✅ | ❌ |
| rollback | ✅ | ✅ | ❌ |
| start | ✅ | ❌ | ❌ |
| stop | ✅ | ❌ | ❌ |
| restart | ✅ | ❌ | ❌ |

### Adding Users

**Via Command (Admin only):**
```
/adduser 987654321 developer
```

**Via Config File:**
Edit `app/config.py`:
```python
RBAC_CONFIG = {
    "admin": [123456789],
    "developer": [987654321, 111222333],
    "viewer": [444555666]
}
```

---

## 📊 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    TELEGRAM USERS                           │
│           (Admin / Developer / Viewer)                      │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   TELEGRAM BOT API                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    CHATOPS BOT                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Command   │  │     NLP     │  │    Notification     │  │
│  │  Handlers   │  │   Handler   │  │      Service        │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                     │            │
│         └────────────────┼─────────────────────┘            │
│                          │                                  │
│                   ┌──────▼──────┐                           │
│                   │    RBAC     │                           │
│                   │   Service   │                           │
│                   └──────┬──────┘                           │
│                          │                                  │
│                   ┌──────▼──────┐                           │
│                   │   Docker    │                           │
│                   │   Service   │                           │
│                   └──────┬──────┘                           │
└──────────────────────────┼──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    DOCKER ENGINE                            │
│    ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│    │Container1│  │Container2│  │Container3│  │   ...    │   │
│    └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | Required |
| `NOTIFICATION_CHAT_ID` | Chat ID for alerts | Optional |
| `LOG_LEVEL` | Logging level | INFO |
| `HEALTH_CHECK_INTERVAL` | Health check interval (sec) | 60 |
| `MAX_LOG_LINES` | Max log lines to return | 50 |

---

## 🛠️ Development

### Running Tests
```bash
pip install pytest
pytest tests/
```

### View Logs
```bash
# Docker logs
docker-compose logs -f chatops-bot

# Application logs
tail -f logs/chatops.log
```

---

## 📸 Screenshots

### Bot Commands
```
👋 Welcome to ChatOps DevOps Bot!

Hello, Sumit!

🆔 Your User ID: 123456789
👤 Your Role: admin

✅ Your Permissions: deploy, rollback, status, logs, restart, stop, start, stats, list, health
```

### Container List
```
📦 Containers:

🟢 nginx-proxy
   ID: abc123
   Image: nginx:latest
   Status: running
   Ports: 80->80/tcp

🔴 old-app
   ID: def456
   Image: myapp:v1.0
   Status: exited
```

---

## 🚀 Future Enhancements

- [ ] Discord bot support
- [ ] Web dashboard
- [ ] Kubernetes integration
- [ ] Scheduled deployments
- [ ] Deployment history database
- [ ] Multi-server management
- [ ] Custom alerts via webhooks

---

## 📄 License

MIT License - Feel free to use for personal and commercial projects.

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📞 Support

If you encounter any issues:
1. Check the logs: `docker-compose logs chatops-bot`
2. Verify your bot token is correct
3. Ensure Docker is running
4. Check your user ID is in the config

---

**Made with ❤️ for DevOps Engineers**
