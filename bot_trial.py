#!/usr/bin/env python3
"""
TRIAL/DEMO Version of Advanced Telegram Bot
WARNING: IN THIS VERSION, ALL USERS ARE ADMINS.
USE FOR DEMONSTRATION PURPOSES ONLY.
"""

import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters, ChatJoinRequestHandler
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - [TRIAL BOT] - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TrialTelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.application = Application.builder().token(token).job_queue(None).build()
        
        # Configuration files - USING TRIAL FILES TO AVOID CONFLICTS
        self.WELCOME_FILE = "trial_welcome.txt"
        self.ADMINS_FILE = "trial_admins.json" # Kept for structure, but ignored for auth
        self.LOGS_FILE = "trial_logs.txt"
        self.CONFIG_FILE = "trial_bot_config.json"
        self.USERS_FILE = "trial_users.json"
        self.BROADCAST_FILE = "trial_broadcast_data.json"
        
        # Bot configuration
        self.bot_config = {
            "welcome_image": "",
            "welcome_text": "Welcome to our channel! 🎉 (TRIAL MODE)",
            "signup_url": "",
            "join_group_url": "",
            "download_apk": "",
            "daily_bonuses_url": "",
            "admin_group_id": "",
            "live_chat_enabled": True
        }
        
        # User states for live chat
        self.user_states = {}  # Track user conversation states
        self.admin_states = {}  # Track admin conversation states
        
        # Load configuration
        self.load_config()
        
        # Setup handlers
        self.setup_handlers()
        
    def load_config(self):
        """Load configuration from files"""
        # Load admins (Just to initialize file)
        try:
            with open(self.ADMINS_FILE, 'r') as f:
                self.admins = json.load(f)
        except FileNotFoundError:
            self.admins = []
            self.save_admins()
            
        # Load bot configuration
        try:
            with open(self.CONFIG_FILE, 'r') as f:
                self.bot_config.update(json.load(f))
        except FileNotFoundError:
            self.save_bot_config()
            
        # Load welcome message
        try:
            with open(self.WELCOME_FILE, 'r') as f:
                self.bot_config["welcome_text"] = f.read().strip()
        except FileNotFoundError:
            self.save_welcome()
            
        # Load users
        try:
            with open(self.USERS_FILE, 'r') as f:
                self.users = json.load(f)
        except FileNotFoundError:
            self.users = {}
            self.save_users()
            
    def save_bot_config(self):
        """Save bot configuration to file"""
        with open(self.CONFIG_FILE, 'w') as f:
            json.dump(self.bot_config, f, indent=2)
            
    def save_admins(self):
        """Save admin list to file"""
        with open(self.ADMINS_FILE, 'w') as f:
            json.dump(self.admins, f)
            
    def save_welcome(self):
        """Save welcome message to file"""
        with open(self.WELCOME_FILE, 'w', encoding='utf-8') as f:
            f.write(self.bot_config["welcome_text"])
            
    def save_users(self):
        """Save users to file"""
        with open(self.USERS_FILE, 'w') as f:
            json.dump(self.users, f, indent=2)
            
    def log_join(self, username: str, user_id: int, dm_sent: bool, error: str = None):
        """Log join request details"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "✅ DM Sent" if dm_sent else "❌ DM Failed"
        error_info = f" (Error: {error})" if error else ""
        
        log_entry = f"[{timestamp}] @{username} (ID: {user_id}) - {status}{error_info}\n"
        
        with open(self.LOGS_FILE, 'a') as f:
            f.write(log_entry)
            
    def setup_handlers(self):
        """Setup message handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("admin", self.admin_command))
        self.application.add_handler(CommandHandler("id", self.show_chat_id))
        self.application.add_handler(CommandHandler("exit", self.exit_live_chat))
        
        # Callback query handler for inline buttons
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Message handler for admin responses, live chat, and admin replies
        self.application.add_handler(MessageHandler(
            (filters.TEXT | filters.VOICE | filters.PHOTO | filters.VIDEO | 
             filters.Document.ALL | filters.AUDIO | filters.VIDEO_NOTE | 
             filters.Sticker.ALL | filters.ANIMATION) & ~filters.COMMAND, 
            self.handle_message
        ))
        
        # Join request handler
        self.application.add_handler(ChatJoinRequestHandler(self.handle_join_request))
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        # Store user information
        if str(user.id) not in self.users:
            self.users[str(user.id)] = {
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "joined_date": datetime.now().isoformat()
            }
            self.save_users()
        
        await update.message.reply_text(
            "👋 **Welcome to the Demo Bot!**\n\n"
            "This is a trial version where **everyone is an admin**.\n"
            "Feel free to test all features!\n\n"
            "Try sending `/admin` to see the control panel."
        )
        
        # Send the welcome message
        await self.send_welcome_message(context.bot, user.id)
        
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin command - show admin panel - OPEN TO EVERYONE"""
        # NO SECURITY CHECK HERE FOR TRIAL BOT
        await self.show_admin_panel(update, context)
        
    async def show_chat_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /id command - show chat ID"""
        chat = update.effective_chat
        
        # Show chat information without admin checks
        chat_type = "Channel" if chat.type == "channel" else "Supergroup" if chat.type == "supergroup" else "Group"
        username_info = f"\n**Username:** @{chat.username}" if chat.username else "\n**Username:** None (Private)"
        
        await update.message.reply_text(
            f"📋 **Chat Information (Trial Mode)**\n\n"
            f"**Type:** {chat_type}\n"
            f"**Title:** {chat.title}\n"
            f"**ID:** `{chat.id}`\n"
            f"{username_info}",
            parse_mode='Markdown'
        )
        
    async def show_admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show the admin panel with inline buttons"""
        keyboard = [
            [
                InlineKeyboardButton("📝 Set Welcome Text", callback_data="set_welcome_text"),
                InlineKeyboardButton("🖼️ Set Welcome Image", callback_data="set_welcome_image")
            ],
            [
                InlineKeyboardButton("🔗 Set Signup URL", callback_data="set_signup_url"),
                InlineKeyboardButton("👥 Set Join Group URL", callback_data="set_join_group_url")
            ],
            [
                InlineKeyboardButton("📱 Set Download APK", callback_data="set_download_apk"),
                InlineKeyboardButton("🎁 Set Daily Bonuses URL", callback_data="set_daily_bonuses")
            ],
            [
                InlineKeyboardButton("📱 Set Admin Group", callback_data="set_admin_group"),
                InlineKeyboardButton("⚙️ Bot Configuration", callback_data="bot_config")
            ],
            [
                InlineKeyboardButton("📡 Send Message to All Users", callback_data="send_broadcast"),
                InlineKeyboardButton("👥 View User Stats", callback_data="view_users")
            ],
            [
                InlineKeyboardButton("📑 View Logs", callback_data="view_logs"),
                InlineKeyboardButton("🛑 Stop Bot", callback_data="stop_bot")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🔧 **Trial Admin Panel**\n\n"
            "You have full access to configure this demo bot:",
            reply_markup=reply_markup
        )
        
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline buttons"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = query.from_user.id
        
        # Handle user buttons
        if data == "signup":
            await self.handle_signup(query, context)
            return
            
        elif data == "join_group":
            await self.handle_join_group(query, context)
            return
            
        elif data == "live_chat":
            await self.start_live_chat(query, context)
            return
            
        elif data == "download_hack":
            await self.handle_download_hack(query, context)
            return
            
        elif data == "daily_bonuses":
            await self.handle_daily_bonuses(query, context)
            return
            
        elif data == "exit_live_chat":
            await self.exit_live_chat_from_button(query, context)
            return
        
        # Admin buttons - NO SECURITY CHECK FOR TRIAL BOT
        
        if data == "set_welcome_text":
            self.admin_states[user_id] = "waiting_welcome_text"
            await query.edit_message_text(
                "📝 **Set Welcome Text**\n\n"
                "Send the new welcome message text."
            )
            
        elif data == "set_welcome_image":
            self.admin_states[user_id] = "waiting_welcome_image"
            await query.edit_message_text(
                "🖼️ **Set Welcome Image**\n\n"
                "Send the image you want to use as the welcome image."
            )
            
        elif data == "set_signup_url":
            self.admin_states[user_id] = "waiting_signup_url"
            await query.edit_message_text(
                "🔗 **Set Signup URL**\n\n"
                "Send the URL for the signup button."
            )
            
        elif data == "set_join_group_url":
            self.admin_states[user_id] = "waiting_join_group_url"
            await query.edit_message_text(
                "👥 **Set Join Group URL**\n\n"
                "Send the Telegram group/channel invite link."
            )
            
        elif data == "set_download_apk":
            self.admin_states[user_id] = "waiting_download_apk"
            await query.edit_message_text(
                "📱 **Set Download APK**\n\n"
                "Send the APK file you want users to download."
            )
            
        elif data == "set_daily_bonuses":
            self.admin_states[user_id] = "waiting_daily_bonuses"
            await query.edit_message_text(
                "🎁 **Set Daily Bonuses URL**\n\n"
                "Send the URL for the daily bonuses button."
            )
            
        elif data == "set_admin_group":
            self.admin_states[user_id] = "waiting_admin_group"
            await query.edit_message_text(
                "📱 **Set Admin Group**\n\n"
                "Send the group ID where admin replies should be sent.\n"
                "Use /id command in any group to see its ID."
            )
            
        elif data == "bot_config":
            await self.show_bot_config(query)
            
        elif data == "send_broadcast":
            self.admin_states[user_id] = "waiting_broadcast"
            await query.edit_message_text(
                "📡 **Send Message to All Users**\n\n"
                "Send the message you want to broadcast."
            )
            
        elif data == "view_users":
            await self.show_user_stats(query)
            
        elif data == "view_logs":
            await self.show_logs(query)
            
        elif data == "stop_bot":
            await self.stop_bot(query)
            
        elif data == "back_to_admin":
            await self.show_admin_panel_from_query(query, context)
            
    async def show_bot_config(self, query):
        """Show current bot configuration"""
        config_text = f"""
🔧 **Bot Configuration (Trial)**

📝 **Welcome Text:** {self.bot_config['welcome_text'][:50]}...
🖼️ **Welcome Image:** {'✅ Set' if self.bot_config['welcome_image'] else '❌ Not Set'}
🔗 **Signup URL:** {self.bot_config['signup_url'] or '❌ Not Set'}
👥 **Join Group URL:** {self.bot_config['join_group_url'] or '❌ Not Set'}
📱 **Download APK:** {'✅ Set' if self.bot_config['download_apk'] else '❌ Not Set'}
🎁 **Daily Bonuses URL:** {self.bot_config['daily_bonuses_url'] or '❌ Not Set'}
📱 **Admin Group ID:** {self.bot_config['admin_group_id'] or '❌ Not Set'}
💬 **Live Chat:** {'✅ Enabled' if self.bot_config['live_chat_enabled'] else '❌ Disabled'}
        """.strip()
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="back_to_admin")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(config_text, reply_markup=reply_markup)
        
    async def show_user_stats(self, query):
        """Show user statistics"""
        total_users = len(self.users)
        
        await query.edit_message_text(
            f"👥 **User Statistics (Trial)**\n\n"
            f"📊 **Total Users:** {total_users}\n",
            reply_markup=InlineKeyboardMarkup([[ 
                InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="back_to_admin")
            ]])
        )
        
    async def show_logs(self, query):
        """Show recent logs"""
        try:
            with open(self.LOGS_FILE, 'r') as f:
                logs = f.readlines()
                
            if not logs:
                await query.edit_message_text(
                    "📑 **No Logs Available**",
                    reply_markup=InlineKeyboardMarkup([[ 
                        InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="back_to_admin")
                    ]])
                )
                return
                
            recent_logs = logs[-10:]
            log_text = "📑 **Recent Logs (Trial)**\n\n" + "".join(recent_logs)
            
            if len(log_text) > 4000:
                log_text = log_text[:4000] + "..."
                
            await query.edit_message_text(
                log_text,
                reply_markup=InlineKeyboardMarkup([[ 
                    InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="back_to_admin")
                ]])
            )
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ Error: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[ 
                    InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="back_to_admin")
                ]])
            )
            
    async def stop_bot(self, query):
        """Stop the bot"""
        await query.edit_message_text(
            "🛑 **Bot Stopped**\n\nTrial bot has been stopped.",
            reply_markup=InlineKeyboardMarkup([[ 
                InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="back_to_admin")
            ]])
        )
        os._exit(0) # Force exit for trial bot
        
    async def show_admin_panel_from_query(self, query, context):
        """Show admin panel from callback query"""
        await self.show_admin_panel(update=query, context=context)
        
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages"""
        user_id = update.effective_user.id
        message = update.message
        
        # Admin configuration handling
        if user_id in self.admin_states:
            state = self.admin_states[user_id]
            await self.handle_admin_response(update, context, state)
            return
            
        # Live chat handling
        if user_id in self.user_states and self.user_states[user_id] == "live_chat":
             # Check for exit command
            if message.text and message.text.lower() in ['/exit', '/stop', 'exit']:
                del self.user_states[user_id]
                await message.reply_text("🔙 **Live Chat Ended**")
                return
            
            await self.forward_to_admin_group(update, context, user_id)
            return
            
        # Admin Reply handling (simulate admin reply in admin group)
        if str(message.chat.id) == self.bot_config.get("admin_group_id") and message.reply_to_message:
            await self.handle_admin_reply(update, context)
            return
            
    async def handle_admin_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE, state: str):
        """Handle admin responses for configuration"""
        message = update.message
        user_id = update.effective_user.id
        
        if state == "waiting_welcome_text":
            self.bot_config["welcome_text"] = message.text
            self.save_welcome()
            await message.reply_text("✅ Welcome text updated!")
            
        elif state == "waiting_welcome_image":
            if message.photo:
                self.bot_config["welcome_image"] = message.photo[-1].file_id
                self.save_bot_config()
                await message.reply_text("✅ Welcome image updated!")
            else:
                await message.reply_text("❌ Please send an image.")
                
        elif state == "waiting_signup_url":
            self.bot_config["signup_url"] = message.text
            self.save_bot_config()
            await message.reply_text("✅ Signup URL updated!")
                
        elif state == "waiting_join_group_url":
            self.bot_config["join_group_url"] = message.text
            self.save_bot_config()
            await message.reply_text("✅ Join group URL updated!")
                
        elif state == "waiting_download_apk":
            if message.document:
                self.bot_config["download_apk"] = message.document.file_id
                self.save_bot_config()
                await message.reply_text("✅ Download APK updated!")
            else:
                await message.reply_text("❌ Please send a file.")
                
        elif state == "waiting_daily_bonuses":
            self.bot_config["daily_bonuses_url"] = message.text
            self.save_bot_config()
            await message.reply_text("✅ Daily bonuses URL updated!")
                
        elif state == "waiting_admin_group":
            try:
                self.bot_config["admin_group_id"] = str(message.text)
                self.save_bot_config()
                await message.reply_text(f"✅ Admin group set to: {message.text}")
            except:
                await message.reply_text("❌ Invalid ID")
                
        elif state == "waiting_broadcast":
            await self.broadcast_message_to_all_users(message, context)
            
        # Clear state
        if user_id in self.admin_states:
            del self.admin_states[user_id]
            
    async def forward_to_admin_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Forward user message to admin group"""
        if not self.bot_config["admin_group_id"]:
            await update.message.reply_text("❌ Admin group not configured (Trial Mode).")
            return
            
        try:
            user_info = self.users.get(str(user_id), {})
            username = user_info.get('username', 'No username')
            
            header = f"👤 User: @{username}\n🆔 ID: {user_id}\n💬 Message:\n\n"
            
            if update.message.text:
                await context.bot.send_message(
                    chat_id=self.bot_config["admin_group_id"],
                    text=header + update.message.text
                )
            # (Simplified forwarding for trial - can add media types if needed)
            else:
                await context.bot.send_message(
                    chat_id=self.bot_config["admin_group_id"],
                    text=header + "[Media Message]"
                )
                
            await update.message.reply_text("✅ Sent to admin (Simulated)")
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error forwarding: {e}")
            
    async def handle_admin_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin replies"""
        message = update.message
        if not message.reply_to_message: return
        
        reply_text = message.reply_to_message.text or ""
        import re
        user_id_match = re.search(r'🆔 ID: (\d+)', reply_text)
        
        if not user_id_match: return
        
        user_id = int(user_id_match.group(1))
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"💬 Admin Reply:\n\n{message.text or '[Media]'}"
            )
            await message.reply_text("✅ Reply sent!")
        except Exception as e:
            await message.reply_text(f"❌ Error: {e}")
            
    async def exit_live_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Force exit live chat"""
        user_id = update.effective_user.id
        if user_id in self.user_states:
            del self.user_states[user_id]
            await update.message.reply_text("Live chat ended.")
        else:
            await update.message.reply_text("Not in live chat.")
            
    async def broadcast_message_to_all_users(self, message, context):
        """Broadcast simulation"""
        await message.reply_text(f"📡 Broadcasting to {len(self.users)} users (Trial)...")
        # In trial, just pretend or send to self
        await message.reply_text("✅ Broadcast complete (Simulation)")
            
    async def handle_join_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle join requests"""
        join_request = update.chat_join_request
        try:
            await context.bot.approve_chat_join_request(
                chat_id=join_request.chat.id,
                user_id=join_request.from_user.id
            )
            await self.send_welcome_message(context.bot, join_request.from_user.id)
            self.log_join(join_request.from_user.username, join_request.from_user.id, True)
        except Exception as e:
            self.log_join(join_request.from_user.username, join_request.from_user.id, False, str(e))
            
    async def send_welcome_message(self, bot, user_id: int):
        """Send welcome message"""
        keyboard = []
        if self.bot_config["signup_url"]:
            keyboard.append([InlineKeyboardButton("🔑 Signup", url=self.bot_config["signup_url"])] )
        if self.bot_config["join_group_url"]:
            keyboard.append([InlineKeyboardButton("📢 Join Group", url=self.bot_config["join_group_url"])] )
        
        keyboard.append([InlineKeyboardButton("💬 Live Chat", callback_data="live_chat")])
        
        if self.bot_config["download_apk"]:
            keyboard.append([InlineKeyboardButton("📥 Download Hack", callback_data="download_hack")])
        if self.bot_config["daily_bonuses_url"]:
            keyboard.append([InlineKeyboardButton("🎁 Daily Bonuses", url=self.bot_config["daily_bonuses_url"])] )
            
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        
        try:
            if self.bot_config["welcome_image"]:
                await bot.send_photo(chat_id=user_id, photo=self.bot_config["welcome_image"], caption=self.bot_config["welcome_text"], reply_markup=reply_markup)
            else:
                await bot.send_message(chat_id=user_id, text=self.bot_config["welcome_text"], reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Welcome send error: {e}")

    # Button handlers same as before, simplified
    async def handle_signup(self, query, context): await query.answer("🔑 Signup Link!")
    async def handle_join_group(self, query, context): await query.answer("📢 Join Group!")
    async def handle_download_hack(self, query, context): 
        if self.bot_config["download_apk"]:
            await context.bot.send_document(chat_id=query.from_user.id, document=self.bot_config["download_apk"], caption="APK File!")
            await query.answer("Sent!")
        else: await query.answer("Not configured", show_alert=True)
    async def handle_daily_bonuses(self, query, context): await query.answer("🎁 Bonus Link!")

    async def start_live_chat(self, query, context):
        user_id = query.from_user.id
        self.user_states[user_id] = "live_chat"
        await context.bot.send_message(chat_id=user_id, text="💬 Live chat started (Trial). Type /exit to end.")
        await query.answer()
        
    async def exit_live_chat_from_button(self, query, context):
        user_id = query.from_user.id
        if user_id in self.user_states: del self.user_states[user_id]
        await query.edit_message_text("Live chat ended.")
            
    def run(self):
        print("🚀 Starting TRIAL Bot...")
        self.application.run_polling()

def main():
    token = os.getenv("TRIAL_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ Error: TRIAL_BOT_TOKEN or TELEGRAM_BOT_TOKEN not set!")
        return
    
    print(f"⚠️  STARTING IN TRIAL MODE - USING TOKEN: {token[:10]}...")
    bot = TrialTelegramBot(token)
    bot.run()

if __name__ == "__main__":
    main()
