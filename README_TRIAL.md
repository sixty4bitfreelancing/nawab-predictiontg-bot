# 🤖 Trial/Demo Bot Guide

This is a special version of the bot designed for **demonstration purposes**.

## ⚠️ Important Differences

1.  **Open Access:** ALL users have access to the `/admin` panel and all configuration buttons. There are no security checks.
2.  **Separate Configuration:** This bot uses separate configuration files (prefixed with `trial_`) so it won't mess up your main bot's settings.
3.  **Simulated Features:** Some features like broadcasting might be simulated or simplified for safety.

## 🚀 How to Run

### Option 1: Using the same token (Not Recommended)
If you stop your main bot, you can run this trial bot using the same token.
```bash
./start_trial.sh
```

### Option 2: Using a dedicated Trial Token (Recommended)
Get a new bot token from @BotFather for your demo bot.

```bash
# Export the token
export TRIAL_BOT_TOKEN="your_trial_bot_token_here"

# Run the script
./start_trial.sh
```

## 🎮 What Clients Can Do

-   Send `/start` to see the welcome message.
-   Send `/admin` to open the full admin panel (normally restricted).
-   Click all the buttons to see how they work.
-   Configure settings (changes will be saved to `trial_bot_config.json`).

## 📁 Files Created
-   `bot_trial.py`: The modified bot code.
-   `trial_bot_config.json`: Config for the demo.
-   `trial_users.json`: Users who joined the demo.
-   `trial_logs.txt`: Demo logs.

## ☁️ VPS Hosting
Want to run this trial bot 24/7? Check out the [VPS Deployment Guide](VPS_DEPLOYMENT_TRIAL.md).
