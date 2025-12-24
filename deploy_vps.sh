#!/bin/bash

# 🚀 Advanced Telegram Bot VPS Deployment Script
# This script will deploy your bot to a VPS with proper setup

set -e  # Exit on any error

echo "🤖 Starting Advanced Telegram Bot VPS Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root. Please run as a regular user with sudo privileges."
   exit 1
fi

# Update system packages
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
print_status "Installing required packages..."
sudo apt install -y python3 python3-pip python3-venv git curl wget htop nginx supervisor

# Create bot directory
BOT_DIR="/home/$USER/telegram-bot"
print_status "Creating bot directory: $BOT_DIR"
mkdir -p $BOT_DIR
cd $BOT_DIR

# Clone or copy bot files
if [ -d "Ram-TG-BOT-auto-accepter" ]; then
    print_status "Bot directory already exists, updating..."
    cd Ram-TG-BOT-auto-accepter
    git pull origin main
else
    print_status "Cloning bot repository..."
    git clone https://github.com/sixtyfourbitsquad/Ram-TG-BOT-auto-accepter.git
    cd Ram-TG-BOT-auto-accepter
fi

# Create Python virtual environment
print_status "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create environment file
print_status "Setting up environment configuration..."
if [ ! -f .env ]; then
    cp env.example .env
    print_warning "Please edit .env file with your bot token:"
    print_warning "TELEGRAM_BOT_TOKEN=your_bot_token_here"
    print_warning "Press Enter when ready to continue..."
    read
fi

# Create systemd service file
print_status "Creating systemd service..."
sudo tee /etc/systemd/system/telegram-bot.service > /dev/null <<EOF
[Unit]
Description=Advanced Telegram Bot
After=network.target
Wants=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$BOT_DIR/Ram-TG-BOT-auto-accepter
Environment=PATH=$BOT_DIR/Ram-TG-BOT-auto-accepter/venv/bin
ExecStart=$BOT_DIR/Ram-TG-BOT-auto-accepter/venv/bin/python bot_advanced.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Create supervisor configuration
print_status "Setting up supervisor configuration..."
sudo tee /etc/supervisor/conf.d/telegram-bot.conf > /dev/null <<EOF
[program:telegram-bot]
command=$BOT_DIR/Ram-TG-BOT-auto-accepter/venv/bin/python bot_advanced.py
directory=$BOT_DIR/Ram-TG-BOT-auto-accepter
user=$USER
autostart=true
autorestart=true
stderr_logfile=/var/log/telegram-bot.err.log
stdout_logfile=/var/log/telegram-bot.out.log
environment=PATH="$BOT_DIR/Ram-TG-BOT-auto-accepter/venv/bin"
EOF

# Create log directory
print_status "Setting up logging..."
sudo mkdir -p /var/log/telegram-bot
sudo chown $USER:$USER /var/log/telegram-bot

# Set proper permissions
print_status "Setting file permissions..."
chmod +x bot_advanced.py
chmod 600 .env

# Create startup script
print_status "Creating startup script..."
cat > start_bot.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python bot_advanced.py
EOF

chmod +x start_bot.sh

# Create stop script
print_status "Creating stop script..."
cat > stop_bot.sh << 'EOF'
#!/bin/bash
echo "Stopping Telegram Bot..."
sudo systemctl stop telegram-bot
sudo supervisorctl stop telegram-bot
echo "Bot stopped!"
EOF

chmod +x stop_bot.sh

# Create restart script
print_status "Creating restart script..."
cat > restart_bot.sh << 'EOF'
#!/bin/bash
echo "Restarting Telegram Bot..."
sudo systemctl restart telegram-bot
sudo supervisorctl restart telegram-bot
echo "Bot restarted!"
EOF

chmod +x restart_bot.sh

# Create status script
print_status "Creating status script..."
cat > status_bot.sh << 'EOF'
#!/bin/bash
echo "=== Telegram Bot Status ==="
echo "Systemd Service:"
sudo systemctl status telegram-bot --no-pager -l
echo ""
echo "Supervisor Status:"
sudo supervisorctl status telegram-bot
echo ""
echo "Recent Logs:"
sudo journalctl -u telegram-bot -n 20 --no-pager
EOF

chmod +x status_bot.sh

# Create logs script
print_status "Creating logs script..."
cat > view_logs.sh << 'EOF'
#!/bin/bash
echo "=== Telegram Bot Logs ==="
echo "Systemd Logs:"
sudo journalctl -u telegram-bot -f
EOF

chmod +x view_logs.sh

# Enable and start services
print_status "Enabling and starting services..."
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot

sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start telegram-bot

# Create Nginx configuration (optional, for web interface if needed)
print_status "Setting up Nginx configuration..."
sudo tee /etc/nginx/sites-available/telegram-bot > /dev/null <<EOF
server {
    listen 80;
    server_name _;
    
    location / {
        return 200 "Telegram Bot is running!";
        add_header Content-Type text/plain;
    }
    
    location /status {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

# Enable Nginx site (optional)
sudo ln -sf /etc/nginx/sites-available/telegram-bot /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Create firewall rules
print_status "Setting up firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Create monitoring script
print_status "Creating monitoring script..."
cat > monitor_bot.sh << 'EOF'
#!/bin/bash
echo "=== Telegram Bot Monitor ==="
echo "Timestamp: $(date)"
echo ""

# Check if bot is running
if sudo systemctl is-active --quiet telegram-bot; then
    echo "✅ Bot Status: RUNNING"
else
    echo "❌ Bot Status: STOPPED"
fi

# Check supervisor
if sudo supervisorctl status telegram-bot | grep -q "RUNNING"; then
    echo "✅ Supervisor: RUNNING"
else
    echo "❌ Supervisor: STOPPED"
fi

# Check logs
echo ""
echo "📊 Recent Log Entries:"
sudo journalctl -u telegram-bot -n 5 --no-pager --no-hostname

# Check disk usage
echo ""
echo "💾 Disk Usage:"
df -h $PWD

# Check memory usage
echo ""
echo "🧠 Memory Usage:"
free -h

# Check bot process
echo ""
echo "🔍 Bot Process:"
ps aux | grep "bot_advanced.py" | grep -v grep || echo "No bot process found"
EOF

chmod +x monitor_bot.sh

# Create backup script
print_status "Creating backup script..."
cat > backup_bot.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/$USER/backups"
mkdir -p $BACKUP_DIR

BACKUP_FILE="telegram-bot-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
tar -czf "$BACKUP_DIR/$BACKUP_FILE" \
    --exclude=venv \
    --exclude=__pycache__ \
    --exclude=*.log \
    .

echo "✅ Backup created: $BACKUP_DIR/$BACKUP_FILE"
echo "📁 Backup size: $(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)"
EOF

chmod +x backup_bot.sh

# Create update script
print_status "Creating update script..."
cat > update_bot.sh << 'EOF'
#!/bin/bash
echo "🔄 Updating Telegram Bot..."

# Stop bot
sudo systemctl stop telegram-bot
sudo supervisorctl stop telegram-bot

# Backup current version
./backup_bot.sh

# Pull latest changes
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart bot
sudo systemctl start telegram-bot
sudo supervisorctl start telegram-bot

echo "✅ Bot updated and restarted!"
EOF

chmod +x update_bot.sh

# Final status check
print_status "Performing final status check..."
sleep 5

if sudo systemctl is-active --quiet telegram-bot; then
    print_success "Telegram Bot is running successfully!"
else
    print_error "Bot failed to start. Check logs with: sudo journalctl -u telegram-bot -f"
    exit 1
fi

# Display useful commands
echo ""
print_success "🎉 VPS Deployment Complete!"
echo ""
echo "📋 Useful Commands:"
echo "  Start Bot:     ./start_bot.sh"
echo "  Stop Bot:      ./stop_bot.sh"
echo "  Restart Bot:   ./restart_bot.sh"
echo "  Check Status:  ./status_bot.sh"
echo "  View Logs:     ./view_logs.sh"
echo "  Monitor Bot:   ./monitor_bot.sh"
echo "  Backup Bot:    ./backup_bot.sh"
echo "  Update Bot:    ./update_bot.sh"
echo ""
echo "🔧 Service Management:"
echo "  sudo systemctl status telegram-bot"
echo "  sudo systemctl restart telegram-bot"
echo "  sudo journalctl -u telegram-bot -f"
echo ""
echo "📁 Bot Directory: $BOT_DIR/Ram-TG-BOT-auto-accepter"
echo "📝 Environment File: $BOT_DIR/Ram-TG-BOT-auto-accepter/.env"
echo ""
print_warning "⚠️  Don't forget to edit .env file with your bot token!"
print_warning "⚠️  Make sure your bot token is correct in the .env file!"
echo ""
print_success "🚀 Your Advanced Telegram Bot is now running on VPS!"
