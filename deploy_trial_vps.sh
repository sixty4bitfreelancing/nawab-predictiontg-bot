#!/bin/bash

# 🚀 Trial Telegram Bot VPS Deployment Script
# This script will deploy your TRIAL bot to a VPS

set -e  # Exit on any error

echo "🤖 Starting Trial Bot VPS Deployment..."

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_status "Running as root user."
   SUDO=""
else
   SUDO="sudo"
fi

# Get current directory
BOT_DIR=$(pwd)
print_status "Deploying in directory: $BOT_DIR"

# Update system & install dependencies
print_status "Installing system packages..."
$SUDO apt update && $SUDO apt install -y python3 python3-pip python3-venv htop

# Create virtual environment
print_status "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Setup Token
if [ ! -f .env ]; then
    print_status "Configuring Bot Token..."
    read -p "Enter your TRIAL BOT TOKEN: " TOKEN
    echo "TRIAL_BOT_TOKEN=$TOKEN" > .env
    echo "TELEGRAM_BOT_TOKEN=$TOKEN" >> .env # Fallback
else
    print_status ".env file found. Using existing configuration."
fi

# Create systemd service
SERVICE_NAME="telegram-bot-trial"
print_status "Creating systemd service: $SERVICE_NAME"

$SUDO tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=Trial Telegram Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$BOT_DIR
Environment=PATH=$BOT_DIR/venv/bin
ExecStart=$BOT_DIR/venv/bin/python bot_trial.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Start Service
print_status "Starting service..."
$SUDO systemctl daemon-reload
$SUDO systemctl enable $SERVICE_NAME
$SUDO systemctl restart $SERVICE_NAME

# Final Check
sleep 3
if systemctl is-active --quiet $SERVICE_NAME; then
    print_success "Trial Bot is RUNNING! 🚀"
    echo "Check logs with: $SUDO journalctl -u $SERVICE_NAME -f"
else
    print_error "Bot failed to start. Check logs."
    exit 1
fi
