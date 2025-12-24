#!/bin/bash
# Start the Trial/Demo Bot

# Load environment variables if they exist
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

echo "🚀 Starting Trial Bot..."
echo "To use a specific token for the trial bot, export TRIAL_BOT_TOKEN='your_token' before running this script."
echo "Otherwise, it will use the TELEGRAM_BOT_TOKEN from .env"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Using virtual environment..."
    source venv/bin/activate
fi

python3 bot_trial.py
