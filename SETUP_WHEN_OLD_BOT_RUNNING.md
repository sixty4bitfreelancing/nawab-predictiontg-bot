# Setup / update when your old bot is already running

Use this when you already have this bot running on a VPS (or locally) and want to **update to the latest code** from GitHub without breaking the running bot.

---

## Option A: Update the same bot (replace old code, restart)

**Use this when:** You have one bot running and want it to run the new code (multi-admin, custom buttons, 25 msg/s broadcast, etc.). Short downtime = one restart.

### 1. SSH into your VPS (or open the folder where the bot runs)

```bash
ssh your_user@your_vps_ip
cd /path/to/your/bot   # e.g. /home/adii/bots/nawab-predictiontg-bot
```

### 2. Pull the latest code

```bash
git fetch nawab
git checkout main
git pull nawab main
```

If you use `origin` instead of `nawab`:

```bash
git pull origin main
```

### 3. Install dependencies (if needed)

```bash
source venv/bin/activate   # if you use a venv
pip install -r requirements.txt
```

### 4. Restart the bot

**If you use systemd (recommended):**

```bash
sudo systemctl restart telegram-bot-nawab
# or whatever your service name is, e.g. tg-bot
```

**If you run it manually (e.g. in screen/tmux):**

- Go to the terminal where the bot is running.
- Stop it: `Ctrl+C`.
- Start again: `python run_bot_v2.py` (or `python -m bot.main`).

**Result:** Same bot, same `.env`, same database. Only the code is new. Downtime = a few seconds while it restarts.

---

## Option B: Keep old bot running and run the new code as a second bot

**Use this when:** You want to test the new code in a **different** bot (different token, different DB) while the old one keeps running.

### 1. Clone the repo in a new folder

```bash
cd /home/adii/bots   # or wherever you keep bots
git clone https://github.com/sixty4bitfreelancing/nawab-predictiontg-bot.git new-bot-folder
cd new-bot-folder
```

### 2. Create a new Python env and install

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. New `.env` and new database

- Copy `.env` from the old bot and put it in the new folder.
- **Change:** `TELEGRAM_BOT_TOKEN` to a **new** bot token (from @BotFather) for the new bot.
- **Change:** `DATABASE_URL` to a **new** database (e.g. create `telegram_bot_new` and a new user), so the new bot has its own DB.

Example:

```env
TELEGRAM_BOT_TOKEN=new_bot_token_from_botfather
DATABASE_URL=postgresql://telegram_bot_new:password@localhost:5432/telegram_bot_new
SUPERADMIN_ID=8510817009
```

### 4. Create the new database and tables

```bash
# Create DB and user (as postgres)
sudo -u postgres psql -c "CREATE USER telegram_bot_new WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "CREATE DATABASE telegram_bot_new OWNER telegram_bot_new;"

# Tables are created on first run
python run_bot_v2.py
# Stop with Ctrl+C after you see "Database tables initialized"
```

### 5. Run the new bot (separate process)

- **Option 1:** Another systemd service (e.g. `telegram-bot-new.service`) pointing to the new folder and new `.env`.
- **Option 2:** Run in a second screen/tmux: `python run_bot_v2.py`.

**Result:** Old bot keeps running. New bot runs in parallel with new token and new DB.

---

## Option C: Same bot, same DB – only update code (no new token, no new DB)

Same as **Option A**: one bot, one DB. Pull code → restart. Your existing `.env` and database stay as they are.

**After update:**

- **Multi-admin:** Use Admin Panel → **👑 Manage Admins** to add/remove admins (no need to edit DB by hand).
- **Welcome buttons:** Admin Panel → **🔘 Custom Welcome Buttons (max 10)** to add/remove buttons (no more fixed Signup/Join/Download/Daily).
- **Preview:** Admin Panel → **👁 Preview Welcome Message** to see what users see.
- **Broadcast:** Default is 25 msg/s. Optional: set `BROADCAST_DELAY_SECONDS=0.04` in `.env` (already the default in code).

---

## Quick checklist (update existing bot)

1. `cd` to bot folder on VPS.
2. `git pull nawab main` (or `git pull origin main`).
3. `pip install -r requirements.txt` (if you added deps).
4. `sudo systemctl restart your-bot-service` (or stop/start manually).
5. Check logs: `sudo journalctl -u your-bot-service -f` or the log file in the repo.

---

## If something goes wrong

- **Old code back:** `git log -1` to see the new commit, then `git reset --hard <previous_commit>` and restart. Or keep a backup of the folder before pulling.
- **DB issues:** The new code does **not** remove columns from `bot_config`. Old keys (e.g. signup_url) are simply unused. Safe to update.
- **.env:** No new required variables. Optional: `BROADCAST_DELAY_SECONDS=0.04`, `BROADCAST_RETRY_AFTER_FALLBACK_SECONDS=5`.
