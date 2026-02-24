# 📘 Detailed VPS Setup Guide – Telegram Bot v2

This guide walks you through setting up the Telegram Bot v2 on a VPS from scratch. Follow the steps in order.

---

## Table of contents

1. [Before you start](#1-before-you-start)
2. [Get a VPS and connect](#2-get-a-vps-and-connect)
3. [Get your Telegram bot token and user ID](#3-get-your-telegram-bot-token-and-user-id)
4. [Prepare the server](#4-prepare-the-server)
5. [Install PostgreSQL](#5-install-postgresql)
6. [Install Python and clone the bot](#6-install-python-and-clone-the-bot)
7. [Configure the bot](#7-configure-the-bot)
8. [Test the bot](#8-test-the-bot)
9. [Run the bot 24/7 with systemd](#9-run-the-bot-247-with-systemd)
10. [Add the bot to your channel](#10-add-the-bot-to-your-channel)
11. [Useful commands and troubleshooting](#11-useful-commands-and-troubleshooting)

---

## 1. Before you start

### What you need

- A **VPS** (Virtual Private Server) with:
  - **OS:** Ubuntu 20.04, 22.04, or 24.04 (or Debian 11+)
  - **RAM:** At least 1 GB (2 GB recommended)
  - **Storage:** At least 20 GB
  - **SSH access** (username + password or SSH key)

- A **Telegram account** and:
  - A **bot token** from [@BotFather](https://t.me/BotFather)
  - Your **Telegram user ID** (for admin access)

- A **private channel or group** where you want the bot to approve join requests (you must be admin there).

### VPS providers (examples)

- [DigitalOcean](https://www.digitalocean.com/) – Droplets from ~$4/month  
- [Vultr](https://www.vultr.com/) – similar pricing  
- [Linode](https://www.linode.com/) – similar  
- [Hetzner](https://www.hetzner.com/) – often cheaper in EU  
- [AWS Lightsail](https://aws.amazon.com/lightsail/) – from ~$3.50/month  

Create a Ubuntu 22.04 (or 20.04) server and note:

- **IP address** (e.g. `164.92.xxx.xxx`)
- **SSH user** (often `root` or `ubuntu` depending on provider)

---

## 2. Get a VPS and connect

### Connect via SSH (from your computer)

**Windows (PowerShell or Command Prompt):**

```bash
ssh root@YOUR_VPS_IP
```

**Mac / Linux:**

```bash
ssh root@YOUR_VPS_IP
```

If your provider gave you a user like `ubuntu`:

```bash
ssh ubuntu@YOUR_VPS_IP
```

- Replace `YOUR_VPS_IP` with the real IP.
- When asked “Are you sure you want to continue connecting?”, type `yes` and press Enter.
- Enter the password (or use SSH key if configured).

When you see a prompt like `root@server:~#`, you are connected.

---

## 3. Get your Telegram bot token and user ID

Do this from your phone or desktop Telegram app.

### 3.1 Create the bot and get the token

1. Open Telegram and search for **@BotFather**.
2. Send: `/newbot`
3. Choose a **name** (e.g. “My Join Bot”).
4. Choose a **username** ending in `bot` (e.g. `my_join_bot`).
5. BotFather will reply with a **token** like:
   ```text
   7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
6. **Copy and save** this token; you will put it in `.env` on the VPS.

### 3.2 Get your Telegram user ID (for admin)

1. In Telegram, search for **@userinfobot**.
2. Start the bot; it will reply with your **Id** (e.g. `123456789`).
3. **Copy and save** this number; you will use it as `SUPERADMIN_ID` in `.env`.

---

## 4. Prepare the server

Run these on the VPS (after SSH in).

### Update the system

```bash
sudo apt update
sudo apt upgrade -y
```

This can take a few minutes.

### (Optional) Create a non-root user

If you are logged in as `root`, you can create a normal user:

```bash
adduser botuser
usermod -aG sudo botuser
```

Then log in as that user:

```bash
su - botuser
```

In the rest of the guide, replace `root` or `botuser` with **your** username. Paths like `/home/root/` or `/home/botuser/` depend on that.

---

## 5. Install PostgreSQL

The bot stores config and users in PostgreSQL.

### Install PostgreSQL

```bash
sudo apt install -y postgresql postgresql-contrib
```

### Start and enable PostgreSQL

```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Create database and user

1. Switch to the PostgreSQL admin user and open the DB shell:

```bash
sudo -u postgres psql
```

2. In the `postgres=#` prompt, run (use a **strong password** instead of `your_secure_password`):

```sql
CREATE USER telegram_bot WITH PASSWORD 'your_secure_password';
CREATE DATABASE telegram_bot OWNER telegram_bot;
\q
```

3. You’ll exit back to the normal shell.

### Check that PostgreSQL is running

```bash
sudo systemctl status postgresql
```

You should see `active (running)`. Press `q` to exit.

### Your database URL

You will use this in `.env` later (replace the password with the one you set):

```text
postgresql://telegram_bot:your_secure_password@localhost:5432/telegram_bot
```

---

## 6. Install Python and clone the bot

### Install Python and Git

```bash
sudo apt install -y python3 python3-pip python3-venv git
```

### Go to your home directory and clone the repo

```bash
cd ~
git clone https://github.com/sixtyfourbitsquad/new-tg-auto-join-bot-feb-22-26.git
cd new-tg-auto-join-bot-feb-22-26
```

You should see folders like `bot/` and files like `run_bot_v2.py`, `requirements.txt`.

### Create a virtual environment and install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
```

Your prompt should start with `(venv)`.

Then:

```bash
pip install -r requirements.txt
```

Wait until it finishes without errors.

---

## 7. Configure the bot

### Create `.env` from the example

```bash
cp env.example .env
```

### Edit `.env`

```bash
nano .env
```

Fill in your values. Example:

```env
TELEGRAM_BOT_TOKEN=7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DATABASE_URL=postgresql://telegram_bot:your_secure_password@localhost:5432/telegram_bot
SUPERADMIN_ID=123456789
```

- **TELEGRAM_BOT_TOKEN** – from @BotFather.  
- **DATABASE_URL** – same as in [section 5](#your-database-url); use the password you set for `telegram_bot`.  
- **SUPERADMIN_ID** – your Telegram user ID from @userinfobot.

Optional (you can leave commented or add later):

```env
# DEBUG=false
# LOG_LEVEL=INFO
# MAINTENANCE=false
```

Save and exit:

- `Ctrl+O`, Enter (save)
- `Ctrl+X` (exit)

### Restrict permissions on `.env`

```bash
chmod 600 .env
```

---

## 8. Test the bot

With the virtual environment still active (`(venv)` in the prompt):

```bash
python run_bot_v2.py
```

You should see something like:

```text
Starting Bot v2...
```

And no Python errors. The first run creates the database tables.

- In Telegram, open your bot and send `/start`. You should get the welcome message.
- Send `/admin`. If you see “Access denied”, check that `SUPERADMIN_ID` in `.env` is **your** user ID.

Stop the bot with `Ctrl+C`. We’ll run it properly in the next step.

---

## 9. Run the bot 24/7 with systemd

So the bot keeps running after you disconnect and restarts if it crashes.

### Find your username and project path

```bash
whoami
pwd
```

Example: user `root`, path `/root/new-tg-auto-join-bot-feb-22-26`. Use **your** values in the next step.

### Create the systemd service file

```bash
sudo nano /etc/systemd/system/telegram-bot-v2.service
```

Paste the following and replace **YOUR_USERNAME** and paths with your actual username and path (e.g. `root` and `/root/new-tg-auto-join-bot-feb-22-26`):

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

If your user is `root`, use `/root/` instead of `/home/root/`:

- `WorkingDirectory=/root/new-tg-auto-join-bot-feb-22-26`
- `Environment=PATH=/root/new-tg-auto-join-bot-feb-22-26/venv/bin`
- `ExecStart=/root/new-tg-auto-join-bot-feb-22-26/venv/bin/python run_bot_v2.py`

Save: `Ctrl+O`, Enter, then `Ctrl+X`.

### Enable and start the service

```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot-v2
sudo systemctl start telegram-bot-v2
```

### Check that it’s running

```bash
sudo systemctl status telegram-bot-v2
```

You should see `active (running)`. Press `q` to exit.

---

## 10. Add the bot to your channel

For **auto-approve join requests** and welcome messages:

1. Open your **private** Telegram channel or group.
2. Add the bot as a member (search by bot username).
3. Make the bot **administrator**:
   - Channel/Group → Edit → Administrators → Add Administrator → choose your bot.
   - Give it at least:
     - **Approve join requests** (if your client shows this).
     - Or **Invite users via link** / **Add new admins** as needed so it can approve.

4. Get the **channel/group ID** (needed for “Admin group” in the bot):
   - Add the bot to the **admin group** where you want to receive live chat messages and replies.
   - In that group, send: `/id`
   - The bot will reply with the chat **ID** (e.g. `-1001234567890`).

5. In Telegram, open your bot and send `/admin`.
6. Use the buttons to:
   - Set welcome text and image.
   - Set **Admin Group** (paste the group ID from step 4).
   - Set Signup URL, Join Group URL, etc.

After that, when someone requests to join your private channel/group, the bot will (if “Auto-Accept” is ON) approve them and send the welcome message.

---

## 11. Useful commands and troubleshooting

### Managing the bot service

| What you want        | Command |
|----------------------|--------|
| Check if bot is running | `sudo systemctl status telegram-bot-v2` |
| View live logs       | `sudo journalctl -u telegram-bot-v2 -f` |
| Restart the bot      | `sudo systemctl restart telegram-bot-v2` |
| Stop the bot         | `sudo systemctl stop telegram-bot-v2` |
| Start again          | `sudo systemctl start telegram-bot-v2` |

Logs are also written to `logs/bot.log` inside the project folder.

### Common issues

| Problem | What to do |
|--------|------------|
| **Database connection failed** | 1. Check PostgreSQL: `sudo systemctl status postgresql`<br>2. Check `.env`: `DATABASE_URL` and password match what you set in PostgreSQL. |
| **TELEGRAM_BOT_TOKEN not set** | 1. Make sure `.env` exists in the project folder.<br>2. Open `.env` and confirm the token line has no spaces: `TELEGRAM_BOT_TOKEN=7123...` |
| **Access denied for /admin** | Set `SUPERADMIN_ID` in `.env` to your Telegram user ID (from @userinfobot), then restart: `sudo systemctl restart telegram-bot-v2`. |
| **Permission denied** when starting | The `User=` in the service file must be the same user who owns the project folder. Fix paths and `User=`, then run `sudo systemctl daemon-reload` and `sudo systemctl restart telegram-bot-v2`. |
| **Bot doesn’t approve join requests** | 1. In the bot, use Admin Panel → “🔄 Toggle Auto-Accept Join” and ensure it’s ON.<br>2. In the channel/group, make the bot admin with “Approve join requests” (or equivalent) permission. |

### Updating the bot after code changes

```bash
cd ~/new-tg-auto-join-bot-feb-22-26
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart telegram-bot-v2
```

(Adjust the path if you used a different folder or user.)

### Maintenance mode (server-only)

To show “Bot is under maintenance” to non-admin users:

1. Edit `.env`: set `MAINTENANCE=true`.
2. Restart: `sudo systemctl restart telegram-bot-v2`.

To turn it off: set `MAINTENANCE=false` in `.env` and restart again. This cannot be changed from the bot, only on the server.

### Firewall (optional but recommended)

```bash
sudo ufw allow 22/tcp
sudo ufw --force enable
```

This allows SSH (22) and blocks other ports by default. The bot only talks out to Telegram; it doesn’t need open inbound ports.

---

## Quick reference: full setup from a clean Ubuntu VPS

If you already have the bot token and user ID, you can run these in order (replace placeholders):

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# PostgreSQL
sudo apt install -y postgresql postgresql-contrib
sudo systemctl start postgresql && sudo systemctl enable postgresql
sudo -u postgres psql -c "CREATE USER telegram_bot WITH PASSWORD 'YOUR_DB_PASSWORD';"
sudo -u postgres psql -c "CREATE DATABASE telegram_bot OWNER telegram_bot;"

# Python and bot
sudo apt install -y python3 python3-pip python3-venv git
cd ~ && git clone https://github.com/sixtyfourbitsquad/new-tg-auto-join-bot-feb-22-26.git
cd new-tg-auto-join-bot-feb-22-26
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Configure (then edit .env with your token, DATABASE_URL, SUPERADMIN_ID)
cp env.example .env && chmod 600 .env
nano .env

# Test
python run_bot_v2.py
# Ctrl+C after you see "Starting Bot v2..."

# Service (replace YOUR_USER and path if different)
sudo nano /etc/systemd/system/telegram-bot-v2.service
# Paste the [Unit]/[Service]/[Install] block and fix User= and paths
sudo systemctl daemon-reload && sudo systemctl enable telegram-bot-v2 && sudo systemctl start telegram-bot-v2
sudo systemctl status telegram-bot-v2
```

After this, add the bot to your channel as in [section 10](#10-add-the-bot-to-your-channel) and configure it via `/admin`.

---

**You’re done.** The bot should be running 24/7 and approving join requests (when the toggle is ON) and sending welcome messages. For more deployment options (e.g. Supervisor), see [VPS_DEPLOYMENT_V2.md](VPS_DEPLOYMENT_V2.md).
