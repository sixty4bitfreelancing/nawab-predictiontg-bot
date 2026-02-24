# 🤖 Hosting Multiple Bots on One VPS

This guide explains how to run **several Telegram bots** on the same VPS: separate folders, one PostgreSQL with **one database per bot**, and one systemd service per bot.

---

## Overview

| Item | Per bot |
|------|--------|
| **Folder** | e.g. `~/bots/nawabpredicationbot`, `~/bots/myotherbot` |
| **Virtual env** | Each folder has its own `venv/` |
| **.env** | Own `TELEGRAM_BOT_TOKEN`, `DATABASE_URL`, `SUPERADMIN_ID` |
| **Database** | One PostgreSQL database per bot (e.g. `telegram_bot_nawab`, `telegram_bot_other`) |
| **Systemd service** | One service per bot (e.g. `nawabpredicationbot.service`, `myotherbot.service`) |

Bots don’t listen on ports; they poll Telegram. So you can run as many as you want on one server without port conflicts.

---

## One-time VPS setup (do once)

### 1. Update system and install base packages

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git
```

### 2. Install PostgreSQL (shared by all bots)

```bash
sudo apt install -y postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 3. Create a parent folder for all bots

```bash
mkdir -p ~/bots
cd ~/bots
```

Keep one directory per bot under `~/bots/`, e.g. `~/bots/nawabpredicationbot`, `~/bots/weatherbot`.

---

## Adding the first bot (or any bot)

Use a short **slug** for the bot (e.g. `nawab`, `weather`, `support`). We’ll use `BOT_SLUG` below.

### Step 1: Create a new PostgreSQL database (one per bot)

```bash
sudo -u postgres psql
```

In the `postgres=#` prompt (replace `BOT_SLUG` and use a strong password):

```sql
-- Example: slug = nawab  →  user and DB = telegram_bot_nawab
CREATE USER telegram_bot_BOT_SLUG WITH PASSWORD 'your_secure_password_here';
CREATE DATABASE telegram_bot_BOT_SLUG OWNER telegram_bot_BOT_SLUG;
\q
```

Example for a bot named “nawab”:

```sql
CREATE USER telegram_bot_nawab WITH PASSWORD 'MyStr0ngPass!';
CREATE DATABASE telegram_bot_nawab OWNER telegram_bot_nawab;
\q
```

Your `DATABASE_URL` for this bot will be:

```text
postgresql://telegram_bot_nawab:MyStr0ngPass!@localhost:5432/telegram_bot_nawab
```

### Step 2: Clone (or copy) the bot code into its own folder

```bash
cd ~/bots
git clone https://github.com/sixty4bitfreelancing/nawab-predictiontg-bot.git nawabpredicationbot
cd nawabpredicationbot
```

Use a **folder name** that identifies the bot (e.g. `nawabpredicationbot`, `weatherbot`). Each bot must be in its **own** directory.

### Step 3: Virtual environment and dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 4: Configure this bot’s .env

```bash
cp env.example .env
nano .env
```

Set **at least** (use this bot’s token and DB only):

```env
TELEGRAM_BOT_TOKEN=this_bot_token_from_botfather
DATABASE_URL=postgresql://telegram_bot_nawab:MyStr0ngPass!@localhost:5432/telegram_bot_nawab
SUPERADMIN_ID=123456789
```

- **TELEGRAM_BOT_TOKEN** – from @BotFather for **this** bot.
- **DATABASE_URL** – the URL for **this** bot’s database (from Step 1). **The host must be `localhost`** (not a hostname or IP) when PostgreSQL is on the same server.
- **SUPERADMIN_ID** – your Telegram user ID (can be the same for all bots).

**Important:** If PostgreSQL runs on this VPS, use exactly `localhost` in the URL, e.g. `postgresql://user:pass@localhost:5432/dbname`. Do not use `127.0.0.1` or another hostname unless you know your DB is elsewhere. If your password contains **`@`**, **`#`**, **`%`** or other special characters, URL-encode them in the URL (e.g. `@` → `%40`, `#` → `%23`).

Save: `Ctrl+O`, Enter, `Ctrl+X`.

```bash
chmod 600 .env
```

### Step 5: Test run

```bash
python run_bot_v2.py
```

You should see “Starting Bot v2...” and no errors. In Telegram, send `/start` to this bot. Stop with `Ctrl+C`.

**If you get `Name or service not known` or `Failed to connect to database`:** the **host** in `DATABASE_URL` is wrong. On the VPS, run:

```bash
nano .env
```

Change the `DATABASE_URL` line so the host is **`localhost`** (and the user, password, and database name match what you created in Step 1). Example:

```env
DATABASE_URL=postgresql://telegram_bot_nawab:YOUR_PASSWORD@localhost:5432/telegram_bot_nawab
```

Save, then run `python run_bot_v2.py` again. Confirm PostgreSQL is running: `sudo systemctl status postgresql`.

### Step 6: Create a systemd service for this bot

Use a **unique service name** per bot (e.g. `nawabpredicationbot`, `weatherbot`). Replace `SERVICE_NAME` and paths.

```bash
sudo nano /etc/systemd/system/SERVICE_NAME.service
```

Example for `nawabpredicationbot` (user `adii`, folder `nawabpredicationbot`):

```ini
[Unit]
Description=Nawab Predication Telegram Bot
After=network.target postgresql.service

[Service]
Type=simple
User=adii
WorkingDirectory=/home/adii/bots/nawabpredicationbot
Environment=PATH=/home/adii/bots/nawabpredicationbot/venv/bin
ExecStart=/home/adii/bots/nawabpredicationbot/venv/bin/python run_bot_v2.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

- **User** – the Linux user that owns the bot folder.
- **WorkingDirectory** – full path to **this** bot’s folder.
- **Environment=PATH** and **ExecStart** – same path, using that folder’s **venv**.

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable nawabpredicationbot
sudo systemctl start nawabpredicationbot
sudo systemctl status nawabpredicationbot
```

---

## Adding a second (or more) bot

Repeat the same steps with **different** names and config:

1. **New DB** – New user and database (e.g. `telegram_bot_weather`, `telegram_bot_support`).
2. **New folder** – e.g. `~/bots/weatherbot` (clone or copy code again).
3. **New venv** – `cd ~/bots/weatherbot`, `python3 -m venv venv`, `source venv/bin/activate`, `pip install -r requirements.txt`.
4. **New .env** – This bot’s `TELEGRAM_BOT_TOKEN` and **this** bot’s `DATABASE_URL` (and optionally same or different `SUPERADMIN_ID`).
5. **New systemd service** – New file, e.g. `weatherbot.service`, with **WorkingDirectory** and **ExecStart** pointing to `~/bots/weatherbot`.

Example second service:

```ini
[Unit]
Description=Weather Telegram Bot
After=network.target postgresql.service

[Service]
Type=simple
User=adii
WorkingDirectory=/home/adii/bots/weatherbot
Environment=PATH=/home/adii/bots/weatherbot/venv/bin
ExecStart=/home/adii/bots/weatherbot/venv/bin/python run_bot_v2.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable weatherbot
sudo systemctl start weatherbot
```

---

## Managing multiple bots

Use the **service name** you chose for each bot.

| Action | Command |
|--------|--------|
| List running bot services | `systemctl list-units '*.service' \| grep -E 'nawab\|weather\|bot'` |
| Status of one bot | `sudo systemctl status nawabpredicationbot` |
| Logs (live) | `sudo journalctl -u nawabpredicationbot -f` |
| Restart one bot | `sudo systemctl restart nawabpredicationbot` |
| Stop one bot | `sudo systemctl stop nawabpredicationbot` |
| Start one bot | `sudo systemctl start nawabpredicationbot` |

Each bot also writes logs to its own folder: `~/bots/BOT_FOLDER/logs/bot.log`.

---

## Quick reference: folder layout

```text
/home/adii/
└── bots/
    ├── nawabpredicationbot/
    │   ├── .env          # This bot’s token + DATABASE_URL for telegram_bot_nawab
    │   ├── venv/
    │   ├── bot/
    │   ├── run_bot_v2.py
    │   └── logs/
    │       └── bot.log
    └── weatherbot/
        ├── .env          # Other token + DATABASE_URL for telegram_bot_weather
        ├── venv/
        ├── bot/
        ├── run_bot_v2.py
        └── logs/
```

**PostgreSQL:** one instance, many databases:

- `telegram_bot_nawab`
- `telegram_bot_weather`
- …

---

## Checklist for each new bot

- [ ] New bot created in @BotFather, token copied
- [ ] New DB and user in PostgreSQL (`telegram_bot_SLUG`)
- [ ] New folder under `~/bots/` (clone or copy code)
- [ ] New venv and `pip install -r requirements.txt`
- [ ] New `.env` with this bot’s token and this bot’s `DATABASE_URL`
- [ ] Test run: `python run_bot_v2.py` then Ctrl+C
- [ ] New systemd service file with correct paths and unique service name
- [ ] `daemon-reload`, `enable`, `start`, `status`

---

## Troubleshooting

| Issue | What to check |
|--------|----------------|
| Wrong bot responds | Each folder must have its **own** `.env` with that bot’s `TELEGRAM_BOT_TOKEN`. |
| Database connection failed | In **that** bot’s `.env`, `DATABASE_URL` must point to **that** bot’s database and use `localhost`. |
| Service won’t start | Paths in the `.service` file must match the bot folder and user; run `whoami` and `pwd` from inside the bot folder. |
| “Module not found” when service runs | The service must use **that** bot’s venv: `ExecStart=.../bots/BOT_FOLDER/venv/bin/python run_bot_v2.py`. |

If you already have one bot (e.g. nawabpredicationbot), add a second by creating a new database, new folder, new `.env`, and new service file; the steps above are the same.
