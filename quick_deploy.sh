#!/bin/bash

# 🚀 Quick VPS Deployment Script
# Simple one-click deployment for your Telegram bot

echo "🤖 Quick VPS Deployment for Advanced Telegram Bot"
echo "=================================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ Don't run as root! Use a regular user with sudo privileges."
   exit 1
fi

# Get bot token
echo ""
echo "📝 Please enter your Telegram bot token:"
echo "   (Get it from @BotFather on Telegram)"
read -p "Bot Token: " BOT_TOKEN

if [ -z "$BOT_TOKEN" ]; then
    echo "❌ Bot token is required!"
    exit 1
fi

echo ""
echo "🔧 Setting up your bot..."

# Update system
echo "📦 Updating system packages..."
sudo apt update -y

# Install dependencies
echo "📥 Installing required packages..."
sudo apt install -y python3 python3-pip python3-venv git

# Create bot directory
BOT_DIR="/home/$USER/telegram-bot"
echo "📁 Creating bot directory: $BOT_DIR"
mkdir -p $BOT_DIR
cd $BOT_DIR

# Clone repository
echo "📥 Cloning bot repository..."
git clone https://github.com/sixtyfourbitsquad/Ram-TG-BOT-auto-accepter.git
cd Ram-TG-BOT-auto-accepter

# Setup Python environment
echo "🐍 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📚 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Create environment file
echo "⚙️  Creating environment configuration..."
cat > .env << EOF
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
EOF

# Create systemd service
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/telegram-bot.service > /dev/null << EOF
[Unit]
Description=Advanced Telegram Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$BOT_DIR/Ram-TG-BOT-auto-accepter
Environment=PATH=$BOT_DIR/Ram-TG-BOT-auto-accepter/venv/bin
ExecStart=$BOT_DIR/Ram-TG-BOT-auto-accepter/venv/bin/python bot_advanced.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
echo "🚀 Starting bot service..."
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot

# Wait a moment and check status
sleep 3

if sudo systemctl is-active --quiet telegram-bot; then
    echo ""
    echo "✅ SUCCESS! Your bot is now running on VPS!"
    echo ""
    echo "📋 Useful Commands:"
    echo "  Check Status:  sudo systemctl status telegram-bot"
    echo "  View Logs:     sudo journalctl -u telegram-bot -f"
    echo "  Restart Bot:   sudo systemctl restart telegram-bot"
    echo "  Stop Bot:      sudo systemctl stop telegram-bot"
    echo ""
    echo "📁 Bot Directory: $BOT_DIR/Ram-TG-BOT-auto-accepter"
    echo "📝 Config File: $BOT_DIR/Ram-TG-BOT-auto-accepter/.env"
    echo ""
    echo "🎯 Next Steps:"
    echo "  1. Send /start to your bot on Telegram"
    echo "  2. Send /admin to access admin panel"
    echo "  3. Configure welcome message and settings"
    echo "  4. Test live chat functionality"
    echo ""
    echo "🚀 Your Advanced Telegram Bot is now live on VPS!"
else
    echo ""
    echo "❌ Bot failed to start. Check logs:"
    echo "   sudo journalctl -u telegram-bot -f"
    exit 1
fi
