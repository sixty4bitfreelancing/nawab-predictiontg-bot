# Detailed Technical Guide for Explaining This Project to ChatGPT

Use this guide when asking ChatGPT to help with this project. Copy and paste the relevant sections as context, or use the entire document as a system prompt.

---

## 1. Project Overview

**Project Name:** Advanced Telegram Bot - Auto-Join & Live Chat  
**Primary File:** `bot_advanced.py`  
**Language:** Python 3.10+  
**Framework:** python-telegram-bot v21.0.1

### Purpose
A Telegram bot designed for **private groups/channels** that:
- Automatically approves join requests (auto-accept)
- Sends configurable welcome messages (image + inline buttons) to new members
- Provides a live chat bridge between users and admins
- Allows admins to broadcast messages and manage bot configuration

### Core Use Case
Typical deployment: A private Telegram channel/group requires approval to join. When a user requests to join, the bot auto-approves and sends a welcome message via DM with buttons for Signup, Join Group, Live Chat, Download APK, and Daily Bonuses.

---

## 2. Architecture Overview

### Design Pattern
- **Single-class architecture:** All bot logic is in `AdvancedTelegramBot`
- **File-based persistence:** No database; JSON and TXT files store config and user data
- **Long polling:** Uses `Application.run_polling()` for updates

### Technology Stack
| Component        | Technology                     |
|-----------------|---------------------------------|
| Bot API         | python-telegram-bot 21.0.1     |
| Config          | python-dotenv 1.0.0            |
| Persistence     | JSON files, plain text         |
| Scheduling      | APScheduler 3.10.4 (in deps)   |

### File Structure
```
├── bot_advanced.py      # Main bot logic (single entry point)
├── bot_config.json      # Bot configuration (URLs, file IDs, admin group)
├── admins.json          # List of admin Telegram user IDs
├── users.json           # User registry: {user_id: {username, first_name, last_name, joined_date}}
├── welcome.txt          # Welcome message text (legacy/fallback)
├── logs.txt             # Append-only join logs and broadcast logs
├── broadcast_data.json  # Last broadcast message (cached for retries)
├── requirements.txt     # Dependencies
├── env.example          # Template for .env
└── .env                 # TELEGRAM_BOT_TOKEN (not committed)
```

---

## 3. Data Flow & Logic

### 3.1 Join Request Flow
```
User requests to join private channel/group
         ↓
ChatJoinRequestHandler → handle_join_request()
         ↓
1. approve_chat_join_request(chat_id, user_id)
2. send_welcome_message() → DM to user with photo + inline buttons
3. log_join() → Append to logs.txt
         ↓
User receives welcome in DM (no need to be in group first)
```

**Important:** The bot must be added as an admin to the channel/group with **“Approve join requests”** permission.

### 3.2 Welcome Message Flow
```
send_welcome_message(bot, user_id)
         ↓
Build InlineKeyboardMarkup from bot_config:
  - Signup        → url (if signup_url set)
  - Join Group    → url (if join_group_url set)
  - Live Chat     → callback_data="live_chat"
  - Download Hack → callback_data="download_hack" (if download_apk set)
  - Daily Bonuses → url (if daily_bonuses_url set)
         ↓
If welcome_image: send_photo(photo, caption=welcome_text, reply_markup)
Else: send_message(text, reply_markup)
```

### 3.3 Live Chat Flow

**User → Admin:**
```
User clicks "Live Chat" → callback_data="live_chat"
         ↓
start_live_chat() → user_states[user_id] = "live_chat"
         ↓
User sends any message (text, photo, voice, etc.)
         ↓
handle_message() sees user_states[user_id] == "live_chat"
         ↓
forward_to_admin_group():
  - Prepends: "👤 User: @username (name)\n🆔 ID: {user_id}\n💬 Message:\n\n"
  - Forwards message to admin_group_id (stored in bot_config)
```

**Admin → User:**
```
Admin replies in admin group to a forwarded message
         ↓
handle_message() detects: chat.id == admin_group_id AND message.reply_to_message
         ↓
handle_admin_reply():
  - Extract user_id from replied message text (regex: 🆔 ID: (\d+))
  - Check user_states[user_id] == "live_chat"
  - Forward admin's message to user as "💬 Admin Reply:\n\n..."
```

**Exit:** User types `/exit` or clicks "Exit Live Chat" → `user_states[user_id]` is deleted.

### 3.4 Admin Configuration Flow
```
Admin sends /admin
         ↓
Check user_id in self.admins
         ↓
show_admin_panel() → Inline keyboard with config options
         ↓
Admin clicks e.g. "Set Welcome Text" → callback_data="set_welcome_text"
         ↓
handle_callback() → admin_states[user_id] = "waiting_welcome_text"
         ↓
Admin sends next message
         ↓
handle_message() → user_id in admin_states → handle_admin_response()
         ↓
handle_admin_response(state):
  - waiting_welcome_text  → save to welcome.txt and bot_config
  - waiting_welcome_image → save photo file_id to bot_config
  - waiting_signup_url    → validate URL, save
  - waiting_join_group_url → validate t.me URL, save
  - waiting_download_apk  → save document file_id
  - waiting_daily_bonuses → validate URL, save
  - waiting_admin_group   → save group ID (int)
  - waiting_broadcast     → broadcast_message_to_all_users()
         ↓
Clear admin_states[user_id]
```

### 3.5 Broadcast Flow
```
Admin selects "Send Message to All Users" → admin_states = "waiting_broadcast"
         ↓
Admin sends message (text/photo/video/voice/audio/document/sticker/animation)
         ↓
broadcast_message_to_all_users():
  1. Serialize message to broadcast_data.json
  2. Iterate self.users (skip admins)
  3. For each user: send via bot (text, photo, etc.)
  4. time.sleep(0.1) between sends (rate limiting)
  5. Count success/failure
  6. log_broadcast() → logs.txt
```

---

## 4. State Management

### In-Memory States (not persisted)
- **user_states:** `{user_id: "live_chat"}` — users currently in live chat
- **admin_states:** `{user_id: "waiting_*"}` — admins in a config wizard step

### Persisted Data
- **admins** — list of Telegram user IDs
- **users** — dict of user info (first seen on /start or join)
- **bot_config** — all config (URLs, file IDs, admin_group_id, etc.)
- **welcome.txt** — welcome text (also mirrored in bot_config)

---

## 5. Handler Registration (setup_handlers)

| Handler Type            | Handler Function        | Purpose                               |
|-------------------------|-------------------------|----------------------------------------|
| CommandHandler("start") | start_command           | Register user, send welcome            |
| CommandHandler("admin") | admin_command           | Admin panel (admin-only)               |
| CommandHandler("id")    | show_chat_id            | Show group/channel ID (group-only)     |
| CommandHandler("exit")  | exit_live_chat          | Exit live chat mode                    |
| CallbackQueryHandler   | handle_callback         | All inline button clicks               |
| MessageHandler          | handle_message          | Non-command messages (admin config, live chat, admin reply) |
| ChatJoinRequestHandler  | handle_join_request     | Auto-approve join requests             |

### Message Routing in handle_message
1. **Admin config:** `user_id in admin_states` → `handle_admin_response()`
2. **Live chat (user):** `user_id in user_states and state == "live_chat"` → `forward_to_admin_group()`
3. **Admin reply:** `chat.id == admin_group_id and message.reply_to_message` → `handle_admin_reply()`

---

## 6. Key Technical Details

### User ID Extraction (Admin Reply)
```python
import re
user_id_match = re.search(r'🆔 ID: (\d+)', reply_text)
user_id = int(user_id_match.group(1))
```
The bot relies on this exact format in the forwarded message header.

### File ID Usage
- `welcome_image` — Telegram photo `file_id` (reusable)
- `download_apk` — Telegram document `file_id` (APK file)

### Admin Group ID
- Stored as string in `bot_config["admin_group_id"]`
- Obtained via `/id` command in the target group (bot must be admin)
- Supergroup IDs are typically negative (e.g. `-4854415124`)

### User Registration
- Users are added to `users.json` on `/start` or implicitly when they interact
- Admins are excluded from the user list for broadcasts
- Structure: `{user_id: {username, first_name, last_name, joined_date}}`

---

## 7. Error Handling & Edge Cases

- **Welcome message fails:** Fallback to text-only send
- **Admin group not set:** Live chat shows "Admin group not configured"
- **User not in live chat:** Admin reply shows "User is no longer in live chat mode"
- **Broadcast:** Per-user try/except; failed users increment `failed_count`, logging continues

---

## 8. Prompt Templates for ChatGPT

### For bug fixes
> This is a Telegram bot using python-telegram-bot v21. The main file is `bot_advanced.py`. [Describe the bug]. The bot uses file-based config (bot_config.json, users.json, admins.json) and in-memory state for live chat and admin configuration wizards. See CHATGPT_PROJECT_GUIDE.md for architecture and data flow.

### For new features
> I'm extending a Telegram auto-join + live chat bot. It has: auto-approve join requests, welcome message with inline buttons, live chat (user ↔ admin group), broadcast, and admin config via inline buttons. All logic is in `bot_advanced.py`, persistence is JSON files. I want to add [feature]. How should I integrate it given the current handler and state flow?

### For refactoring
> The bot uses a single `AdvancedTelegramBot` class with handlers for: start, admin, id, exit, callbacks, messages, and join requests. State is managed via `user_states` (live chat) and `admin_states` (config wizard). Config is in `bot_config.json`. I need to [refactor goal] without breaking the live chat or admin reply flow.

---

## 9. Important Code References

| Function                    | Lines (approx) | Responsibility                        |
|----------------------------|----------------|----------------------------------------|
| `__init__`                 | 43–77          | Load config, setup handlers            |
| `load_config`              | 79–110         | Load admins, bot_config, users, welcome|
| `setup_handlers`           | 142–163        | Register all handlers                  |
| `handle_join_request`      | 911–928        | Approve join, send welcome, log        |
| `send_welcome_message`     | 730–773        | Build keyboard, send photo/message     |
| `handle_message`           | 428–451        | Route to admin/live chat/admin reply   |
| `handle_callback`          | 274–392        | Handle all inline button callbacks     |
| `forward_to_admin_group`   | 454–519        | User → admin group forwarding          |
| `handle_admin_reply`       | 521–604        | Admin group → user reply forwarding    |
| `broadcast_message_to_all_users` | 619–727  | Broadcast to all non-admin users       |

---

## 10. Environment & Dependencies

- **TELEGRAM_BOT_TOKEN:** Required; from @BotFather
- **requirements.txt:**
  - python-telegram-bot==21.0.1
  - APScheduler==3.10.4
  - python-dotenv==1.0.0

Run: `python bot_advanced.py` (after `pip install -r requirements.txt` and setting token in `.env`).

---

*This guide is intended for use with ChatGPT or similar LLMs to provide precise technical context about the project architecture, data flow, and implementation details.*
