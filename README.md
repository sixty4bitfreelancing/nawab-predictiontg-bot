# 🤖 Advanced Telegram Bot - Auto-Join & Live Chat

A powerful Telegram bot that automatically approves join requests, sends welcome messages with inline buttons, and provides live chat functionality with admin support.

## ✨ Features

### 🔄 Auto-Join Request Approval
- Instantly approves join requests to private groups/channels
- Sends personalized welcome messages to new members

### 🎯 Welcome Message System
- **Custom welcome image** (set by admin)
- **Interactive inline buttons:**
  - 🔑 **Signup** → URL set by admin
  - 📢 **Join Group** → Telegram group/channel link
  - 💬 **Live Chat** → Private chat with admin
  - 📥 **Download Hack** → APK file with teasing captions
  - 🎁 **Daily Bonuses** → URL set by admin

### 💬 Live Chat System
- **Full media support:** text, photo, video, voice, audio, document, sticker, GIF
- **Admin reply forwarding** from admin group to users
- **Easy exit button** during live chat
- **User state management**

### 📡 Broadcast Messaging
- Send messages to all users (excluding admins)
- Support for all media types
- Success/failure tracking

### 🔧 Admin Panel
- **Inline button interface** for easy management
- **Bot configuration** (welcome image, text, URLs, APK)
- **User statistics** and logs
- **Admin group management**

## 🚀 Quick Setup

### 1. Prerequisites
- Python 3.10 or higher
- Telegram bot token (get from @BotFather)
- Admin access to a private group/channel

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/sixtyfourbitsquad/Ram-TG-BOT-auto-accepter.git
cd Ram-TG-BOT-auto-accepter

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
```bash
# Set bot token
export TELEGRAM_BOT_TOKEN="your_bot_token_here"

# Or create .env file
cp env.example .env
# Edit .env with your bot token
```

### 4. Add Admin Users
Edit `admins.json` and add your Telegram user ID:
```json
[123456789]
```

### 5. Run the Bot
```bash
python bot_advanced.py
```

## 📁 File Structure

```
├── bot_advanced.py          # Main bot code
├── requirements.txt          # Python dependencies
├── admins.json              # Admin user IDs
├── bot_config.json          # Bot configuration
├── users.json               # User database
├── broadcast_data.json      # Broadcast system
├── logs.txt                 # Activity logs
├── env.example              # Environment template
└── README.md                # This file
```

## 🎮 Usage

### For Regular Users
- Join requests are automatically approved
- Receive welcome message with interactive buttons
- Use live chat for admin support
- Download APK files and access bonuses

### For Admins
1. Send `/admin` to the bot
2. Use inline buttons to configure:
   - Welcome image and text
   - Signup and group URLs
   - Download APK file
   - Admin group ID
   - Broadcast messages

## 🔧 Admin Panel Features

### 📝 Welcome Message Management
- Set custom welcome text
- Upload welcome image
- Configure button URLs

### 📱 Live Chat Management
- Set admin group for live chat
- Monitor user interactions
- Reply to users from admin group

### 📡 Broadcast System
- Send messages to all users
- Track delivery success/failure
- Support all media types

## 🎨 UI Features

- **Teasing text** throughout user experience
- **Emoji-based** visual design
- **Full-width buttons** for better UX
- **Interactive elements** for engagement

## 🔒 Security

- **Admin-only access** to configuration
- **User state management** for live chat
- **Error handling** and logging
- **File validation** and safety checks

## 🚨 Troubleshooting

### Bot not working?
- Check bot token in environment
- Verify admin user ID in `admins.json`
- Check bot permissions in groups

### Live chat not working?
- Ensure admin group ID is set
- Check bot is admin in admin group
- Verify user states are working

### Welcome buttons not working?
- Check button URLs are configured
- Verify bot has proper permissions
- Test with different user accounts

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📄 License

This project is open source and available under the MIT License.

---

**Made with ❤️ for Telegram communities**

*Advanced features for modern Telegram bot management*

