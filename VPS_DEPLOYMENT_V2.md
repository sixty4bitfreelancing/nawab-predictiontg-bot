# 🚀 VPS Deployment Guide - Bot v2 (PostgreSQL)

Deploy the modular Telegram Bot v2 to a VPS with PostgreSQL.

## 📋 Prerequisites

### VPS Requirements
- **OS:** Ubuntu 20.04+ or Debian 11+
- **RAM:** Minimum 1GB (2GB recommended for PostgreSQL)
- **Storage:** Minimum 20GB
- **CPU:** 1 vCPU minimum

### You Need
- Telegram bot token from [@BotFather](https://t.me/BotFather)
- Admin Telegram user ID (for `/admin` and error alerts)
- SSH access to your VPS

---

## 🔧 Step 1: Connect & Update

```bash
ssh username@YOUR_VPS_IP
sudo apt update && sudo apt upgrade -y
```

---

## 🐘 Step 2: Install PostgreSQL

```bash
sudo apt install -y postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

Create database and user:

```bash
sudo -u postgres psql
```

In the PostgreSQL prompt:

```sql
CREATE USER telegram_bot WITH PASSWORD 'your_secure_password';
CREATE DATABASE telegram_bot OWNER telegram_bot;
\q
```

Note your connection string:
`postgresql://telegram_bot:your_secure_password@localhost:5432/telegram_bot`

---

## 🐍 Step 3: Install Python & Dependencies

```bash
sudo apt install -y python3 python3-pip python3-venv git
```

---

## 📂 Step 4: Clone or Upload Code

**Option A: Git clone**

```bash
cd ~
git clone https://github.com/sixtyfourbitsquad/new-tg-auto-join-bot-feb-22-26.git
cd new-tg-auto-join-bot-feb-22-26
```

**Option B: SCP upload (from your computer)**

```bash
scp -r /path/to/TG-Auto-accpet-Trial-Bot/* user@YOUR_VPS_IP:~/new-tg-auto-join-bot/
```

---

## 🔐 Step 5: Configure Environment

```bash
cd ~/new-tg-auto-join-bot-feb-22-26   # or your folder
cp env.example .env
nano .env
```

Edit `.env`:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
DATABASE_URL=postgresql://telegram_bot:your_secure_password@localhost:5432/telegram_bot
SUPERADMIN_ID=123456789

# Optional (production)
# DEBUG=false
# LOG_LEVEL=INFO
```

Save: `Ctrl+X`, then `Y`, then `Enter`.

---

## 🐍 Step 6: Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## ✅ Step 7: Test Run

```bash
python run_bot_v2.py
```

If you see "Starting Bot v2..." and no errors, press `Ctrl+C` to stop. Tables are created on first run.

---

## 🔄 Step 8: Systemd Service (Auto-start)

```bash
sudo nano /etc/systemd/system/telegram-bot-v2.service
```

Paste (replace `YOUR_USERNAME` with your actual username):

```ini
[Unit]
Description=Telegram Bot v2
After=network.target postgresql.service

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/new-tg-auto-join-bot-feb-22-26
Environment=PATH=/home/YOUR_USERNAME/new-tg-auto-join-bot-feb-22-26/venv/bin
ExecStart=/home/YOUR_USERNAME/new-tg-auto-join-bot-feb-22-26/venv/bin/python run_bot_v2.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot-v2
sudo systemctl start telegram-bot-v2
sudo systemctl status telegram-bot-v2
```

---

## 🛠️ Managing the Bot

| Action | Command |
|--------|---------|
| Check status | `sudo systemctl status telegram-bot-v2` |
| View logs | `sudo journalctl -u telegram-bot-v2 -f` |
| Restart | `sudo systemctl restart telegram-bot-v2` |
| Stop | `sudo systemctl stop telegram-bot-v2` |

Logs are also written to `logs/bot.log` in the project directory.

---

## 🔒 Security

### Firewall

```bash
sudo ufw allow 22/tcp
sudo ufw --force enable
```

### Protect .env

```bash
chmod 600 .env
```

### First Admin

Set `SUPERADMIN_ID` in `.env` to your Telegram user ID. Get it by messaging [@userinfobot](https://t.me/userinfobot).

---

## 🔄 Updating the Bot

```bash
cd ~/new-tg-auto-join-bot-feb-22-26
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart telegram-bot-v2
```

---

## ❗ Troubleshooting

| Issue | Fix |
|-------|-----|
| `Database connection failed` | Check PostgreSQL is running: `sudo systemctl status postgresql` |
| `TELEGRAM_BOT_TOKEN not set` | Verify `.env` exists and token is correct |
| `Permission denied` | Ensure bot user owns the project folder |
| Bot not responding | Check logs: `sudo journalctl -u telegram-bot-v2 -n 50` |
