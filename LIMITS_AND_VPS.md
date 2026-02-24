# Bot limits & broadcasting – Telegram API and VPS

## Telegram Bot API limits (what applies to this bot)

- **Sending messages to different users (broadcast):**  
  About **30 messages per second** per bot (global). Sustained: about **900 messages per 30 seconds**.
- **Same chat:** Sending many messages to the same user/group is throttled more (e.g. ~1 per few seconds in groups); this bot mainly does **one welcome per user** and **broadcast to many different users**, so the 30 msg/s limit is the one that matters.
- When you exceed the limit, Telegram returns **429 (RetryAfter)**. The bot already waits the suggested time and retries once per user.

So the **real cap is Telegram’s ~30 msg/s per bot**, not your server.

---

## Broadcast limits in this bot

| Setting | Default | Env variable | Meaning |
|--------|--------|--------------|--------|
| Delay between each send | `0.04` s | `BROADCAST_DELAY_SECONDS` | Pause after every user. 0.04 → **25 messages/second** (under Telegram’s 30/s). |
| Wait when rate-limited | `5` s | `BROADCAST_RETRY_AFTER_FALLBACK_SECONDS` | If Telegram says “slow down” but doesn’t say how long, wait this many seconds before retrying. |

**Rough broadcast duration (with default 25 msg/s):**

- 1,000 users → ~40 seconds  
- 10,000 users → ~6–7 minutes  
- 30,000 users → ~20 minutes  

If you see **429 / RetryAfter** in logs, the bot will wait and retry; you can slow it down by increasing the delay in `.env` (see below).

### Tuning broadcast (optional)

In your bot’s `.env` (same folder as `run_bot_v2.py`):

```env
# Delay between each send (default 0.04 = 25 msg/s)
BROADCAST_DELAY_SECONDS=0.04

# If Telegram says “retry later” but doesn’t say how long (default 5)
BROADCAST_RETRY_AFTER_FALLBACK_SECONDS=5
```

- **Safer / fewer 429s:** e.g. `0.05` (20 msg/s) or `0.1` (10 msg/s).  
- **Default:** `0.04` = **25 msg/s**. Going below ~0.034 is not recommended (Telegram ~30/s).

Restart the bot after changing `.env`.

---

## Your VPS: 4 CPU, 8 GB RAM, 75 GB NVMe

- **CPU/RAM:** This bot is light (one Python process, async I/O, PostgreSQL). 4c/8GB is **more than enough** for:
  - One bot instance
  - Several bot instances (e.g. 3–5 bots, one folder + one DB per bot)
- **Bottleneck:** Telegram’s **30 msg/s per bot** limit. Your server can handle many more requests; the limit is on Telegram’s side.
- **Storage (75 GB):** Logs and PostgreSQL (users, admins, config, join logs, broadcast results) use very little unless you have huge user counts (e.g. millions). 75 GB is plenty for many bots and long-term logs.

**Summary:** With 4c/8GB/75GB you can run **multiple bots** on one VPS. Each bot still obeys Telegram’s 30 msg/s. If you run several bots, each has its own 30 msg/s quota (per token).

---

## Quick reference

| Limit type | Value |
|------------|--------|
| Telegram (send to different users) | ~30 msg/s per bot |
| Bot default broadcast speed | 25 msg/s (0.04 s delay) |
| Tuning | `BROADCAST_DELAY_SECONDS`, `BROADCAST_RETRY_AFTER_FALLBACK_SECONDS` in `.env` |
| VPS capacity | 4c/8GB/75GB is enough for this bot and several more; real limit is Telegram API |
