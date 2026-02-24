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

## Features (optional)

- **Auto-accept toggle** – In Admin Panel use "🔄 Toggle Auto-Accept Join". When OFF, the bot does not approve channel/group join requests; all other services (/start welcome, live chat, broadcast) keep running.
- **Maintenance mode** – Set `MAINTENANCE=true` in `.env` (server only). Non-admin users see a maintenance message; admins can use the bot. Change only by editing `.env` and restarting.

## VPS Deployment

- **[VPS_SETUP_GUIDE.md](VPS_SETUP_GUIDE.md)** – Step-by-step VPS setup (recommended).
- [VPS_DEPLOYMENT_V2.md](VPS_DEPLOYMENT_V2.md) – Shorter deployment reference.
