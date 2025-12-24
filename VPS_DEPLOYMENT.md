# 🚀 VPS Deployment Guide - Advanced Telegram Bot

This guide will help you deploy your advanced Telegram bot to a VPS (Virtual Private Server).

## 📋 Prerequisites

### VPS Requirements
- **OS:** Ubuntu 20.04+ or Debian 11+
- **RAM:** Minimum 1GB (2GB recommended)
- **Storage:** Minimum 20GB
- **CPU:** 1 vCPU minimum
- **Network:** Public IP address

### Bot Requirements
- Telegram bot token from [@BotFather](https://t.me/BotFather)
- Admin user ID for bot management
- Private group/channel for testing

## 🔧 Quick Deployment

### Method 1: Automated Script (Recommended)

1. **Connect to your VPS:**
```bash
ssh username@your_vps_ip
```

2. **Download and run the deployment script:**
```bash
wget https://raw.githubusercontent.com/sixtyfourbitsquad/Ram-TG-BOT-auto-accepter/main/deploy_vps.sh
chmod +x deploy_vps.sh
./deploy_vps.sh
```

3. **Follow the prompts and enter your bot token when asked**

### Method 2: Manual Deployment

1. **Update system:**
```bash
sudo apt update && sudo apt upgrade -y
```

2. **Install dependencies:**
```bash
sudo apt install -y python3 python3-pip python3-venv git curl wget
```

3. **Clone repository:**
```bash
cd /home/$USER
git clone https://github.com/sixtyfourbitsquad/Ram-TG-BOT-auto-accepter.git
cd Ram-TG-BOT-auto-accepter
```

4. **Setup Python environment:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

5. **Configure bot:**
```bash
cp env.example .env
nano .env  # Edit with your bot token
```

6. **Run bot:**
```bash
python bot_advanced.py
```

## 🎯 Advanced Setup

### Systemd Service (Auto-start)

Create a systemd service for automatic startup:

```bash
sudo tee /etc/systemd/system/telegram-bot.service > /dev/null <<EOF
[Unit]
Description=Advanced Telegram Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/Ram-TG-BOT-auto-accepter
Environment=PATH=/home/$USER/Ram-TG-BOT-auto-accepter/venv/bin
ExecStart=/home/$USER/Ram-TG-BOT-auto-accepter/venv/bin/python bot_advanced.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
```

### Supervisor (Process Management)

Install supervisor for better process management:

```bash
sudo apt install -y supervisor
```

Create configuration:
```bash
sudo tee /etc/supervisor/conf.d/telegram-bot.conf > /dev/null <<EOF
[program:telegram-bot]
command=/home/$USER/Ram-TG-BOT-auto-accepter/venv/bin/python bot_advanced.py
directory=/home/$USER/Ram-TG-BOT-auto-accepter
user=$USER
autostart=true
autorestart=true
stderr_logfile=/var/log/telegram-bot.err.log
stdout_logfile=/var/log/telegram-bot.out.log
EOF
```

Start supervisor:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start telegram-bot
```

## 🔒 Security Setup

### Firewall Configuration

```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (if needed)
sudo ufw allow 443/tcp   # HTTPS (if needed)
sudo ufw --force enable
```

### Environment Variables

Create `.env` file with secure configuration:

```bash
# Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Optional: Database (if using)
# DATABASE_URL=postgresql://user:pass@localhost/dbname

# Optional: Redis (if using)
# REDIS_URL=redis://localhost:6379
```

### File Permissions

```bash
chmod 600 .env                    # Restrict env file access
chmod 755 bot_advanced.py         # Make bot executable
chmod 644 *.json                  # Readable config files
```

## 📊 Monitoring & Maintenance

### Status Commands

```bash
# Check bot status
sudo systemctl status telegram-bot

# View logs
sudo journalctl -u telegram-bot -f

# Check supervisor
sudo supervisorctl status telegram-bot

# Monitor resources
htop
```

### Backup Script

Create automated backups:

```bash
#!/bin/bash
BACKUP_DIR="/home/$USER/backups"
mkdir -p $BACKUP_DIR

BACKUP_FILE="telegram-bot-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
tar -czf "$BACKUP_DIR/$BACKUP_FILE" \
    --exclude=venv \
    --exclude=__pycache__ \
    --exclude=*.log \
    .

echo "Backup created: $BACKUP_FILE"
```

### Update Script

```bash
#!/bin/bash
echo "Updating Telegram Bot..."

# Stop bot
sudo systemctl stop telegram-bot

# Backup
./backup_bot.sh

# Pull updates
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart
sudo systemctl start telegram-bot

echo "Update complete!"
```

## 🚨 Troubleshooting

### Common Issues

#### Bot Not Starting
```bash
# Check logs
sudo journalctl -u telegram-bot -f

# Check permissions
ls -la bot_advanced.py
ls -la .env

# Test manually
source venv/bin/activate
python bot_advanced.py
```

#### Permission Denied
```bash
# Fix ownership
sudo chown -R $USER:$USER /home/$USER/Ram-TG-BOT-auto-accepter

# Fix permissions
chmod 755 bot_advanced.py
chmod 600 .env
```

#### Dependencies Missing
```bash
# Reinstall virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Service Not Found
```bash
# Reload systemd
sudo systemctl daemon-reload

# Check service file
sudo systemctl status telegram-bot
```

### Log Locations

- **Systemd logs:** `/var/log/journal/`
- **Supervisor logs:** `/var/log/supervisor/`
- **Bot logs:** `logs.txt` (in bot directory)
- **Nginx logs:** `/var/log/nginx/`

## 🔄 Maintenance Commands

### Daily Operations

```bash
# Check status
./status_bot.sh

# View recent logs
./view_logs.sh

# Monitor resources
./monitor_bot.sh
```

### Weekly Operations

```bash
# Create backup
./backup_bot.sh

# Check for updates
git fetch origin
git status

# Monitor disk usage
df -h
```

### Monthly Operations

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Clean old backups
find /home/$USER/backups -name "*.tar.gz" -mtime +30 -delete

# Check log rotation
sudo logrotate -f /etc/logrotate.conf
```

## 📱 Bot Configuration

### Initial Setup

1. **Set bot token in `.env` file**
2. **Add admin user ID to `admins.json`**
3. **Configure welcome message in admin panel**
4. **Set admin group ID for live chat**
5. **Upload welcome image and APK file**

### Admin Panel Access

Send `/admin` to your bot to access:
- Welcome message configuration
- Live chat settings
- Broadcast messaging
- User statistics
- Bot logs

## 🌟 Advanced Features

### Load Balancing

For high-traffic bots, consider:
- Multiple bot instances
- Nginx load balancer
- Redis for session management
- Database for user storage

### Monitoring

- **Prometheus + Grafana** for metrics
- **Sentry** for error tracking
- **UptimeRobot** for availability
- **Custom health checks**

### Backup Strategies

- **Automated daily backups**
- **Off-site storage** (S3, Google Drive)
- **Database dumps** (if using database)
- **Configuration backups**

## 📞 Support

If you encounter issues:

1. **Check logs first**
2. **Verify configuration**
3. **Test manually**
4. **Check system resources**
5. **Review this guide**

## 🎉 Success!

Your advanced Telegram bot is now running on VPS with:
- ✅ Auto-start on boot
- ✅ Process monitoring
- ✅ Automatic restarts
- ✅ Log management
- ✅ Security hardening
- ✅ Easy maintenance

**Happy botting!** 🤖✨
