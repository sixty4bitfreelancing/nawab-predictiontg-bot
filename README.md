    # Bot v2 - Production-Grade Modular Telegram Bot

## Features

- **Modular structure** - handlers, services, keyboards separated
- **PostgreSQL** - no JSON file storage
- **Global error handling** - structured logging, no raw tracebacks to users
- **Broadcast engine** - RetryAfter, Forbidden, NetworkError handling
- **Admin error reporting** - CRITICAL errors sent to superadmin
- **DEBUG mode** - full traceback when `DEBUG=true`

## Setup

### 1. PostgreSQL

Create database:

```sql
CREATE DATABASE telegram_bot;
```

### 2. Environment

```bash
cp env.example .env
# Edit .env:
# - TELEGRAM_BOT_TOKEN
# - DATABASE_URL (if needed)
# - SUPERADMIN_ID (optional, for error alerts)
# - DEBUG=true (optional, for development)
```

### 3. Install

```bash
pip install -r requirements.txt
```

### 4. Run

```bash
python run_bot_v2.py
```

Or:

```bash
python -m bot.main
```

## Project Structure

```
bot/
├── main.py           # Entry point, handler registration
├── config.py         # Configuration (DEBUG, DATABASE_URL, etc.)
├── database.py       # PostgreSQL pool, init, queries
├── scheduler.py      # APScheduler (for future scheduled tasks)
├── handlers/         # Command and update handlers
├── services/         # Business logic (broadcast, config, user, etc.)
├── keyboards/        # Inline keyboards
├── models/           # Data models
└── utils/            # Logger, exceptions, error handler
```

## Error Handling

- **Global handler** - `application.add_error_handler(global_error_handler)`
- **Custom exceptions** - DatabaseError, BroadcastError, WelcomeBuilderError, SchedulerError, ValidationError
- **Broadcast** - One user failure never crashes the loop; RetryAfter waits and retries
- **Logging** - Structured format: `[timestamp] LEVEL | module | message`

## Admins: Superadmin vs normal admin

- **Superadmin** – The Telegram user whose ID is set as `SUPERADMIN_ID` in `.env`. That person:
  - Is added to the `admins` table on bot startup (so they can use `/admin`).
  - Receives **CRITICAL error alerts** in Telegram (short summary, no full traceback).
  - Get the ID from [@userinfobot](https://t.me/userinfobot) and put it in `.env`.

- **Normal admin** – Any user whose Telegram user ID is in the `admins` table. They can use `/admin`, configure the bot, broadcast, etc. They do **not** receive CRITICAL error alerts (only the superadmin does).

- **How to add more admins** – There is no in-bot “add admin” button. Add them in the database (run on the server, in the same DB as the bot):
  ```sql
  INSERT INTO admins (user_id) VALUES (123456789) ON CONFLICT (user_id) DO NOTHING;
  ```
  Replace `123456789` with the new admin’s Telegram user ID (from @userinfobot).

## Features (optional)

- **Auto-accept toggle** – In Admin Panel use "🔄 Toggle Auto-Accept Join". When OFF, the bot does not approve channel/group join requests; all other services (/start welcome, live chat, broadcast) keep running.
- **Maintenance mode** – Set `MAINTENANCE=true` in `.env` (server only). Non-admin users see a maintenance message; admins can use the bot. Change only by editing `.env` and restarting.

## VPS Deployment

- **[VPS_SETUP_GUIDE.md](VPS_SETUP_GUIDE.md)** – Step-by-step VPS setup (recommended).
- [VPS_DEPLOYMENT_V2.md](VPS_DEPLOYMENT_V2.md) – Shorter deployment reference.
- **[MULTI_BOT_VPS_SETUP.md](MULTI_BOT_VPS_SETUP.md)** – Hosting **multiple bots** on one VPS (one folder and one DB per bot).
