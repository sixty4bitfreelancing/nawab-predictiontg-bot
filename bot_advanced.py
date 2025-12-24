#!/usr/bin/env python3
"""
Advanced Telegram Bot with Welcome Message, Inline Buttons, and Live Chat Forwarding
Features:
- Auto-accept join requests
- Welcome message with customizable image and buttons
- Live chat forwarding between users and admin group
- Admin panel for configuration
- File-based configuration (no database)
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

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class AdvancedTelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.application = Application.builder().token(token).build()
        
        # Configuration files
        self.WELCOME_FILE = "welcome.txt"
        self.ADMINS_FILE = "admins.json"
        self.LOGS_FILE = "logs.txt"
        self.CONFIG_FILE = "bot_config.json"
        self.USERS_FILE = "users.json"
        
        # Bot configuration
        self.bot_config = {
            "welcome_image": "",
            "welcome_text": "Welcome to our channel! 🎉",
            "signup_url": "",
            "join_group_url": "",
            "download_apk": "",
            "daily_bonuses_url": "",
            "admin_group_id": "",
            "live_chat_enabled": True
        }
        
        # Broadcast configuration
        self.broadcast_file = "broadcast_data.json"
        
        # User states for live chat
        self.user_states = {}  # Track user conversation states
        self.admin_states = {}  # Track admin conversation states
        
        # Load configuration
        self.load_config()
        
        # Setup handlers
        self.setup_handlers()
        
    def load_config(self):
        """Load configuration from files"""
        # Load admins
        try:
            with open(self.ADMINS_FILE, 'r') as f:
                self.admins = json.load(f)
        except FileNotFoundError:
            self.admins = [5638736363]  # Default admin
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
        
        # Store user information (but not admin users)
        if str(user.id) not in self.users and user.id not in self.admins:
            self.users[str(user.id)] = {
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "joined_date": datetime.now().isoformat()
            }
            self.save_users()
        
        # Send the same welcome message that users get when joining channels
        await self.send_welcome_message(context.bot, user.id)
        
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin command - show admin panel"""
        user_id = update.effective_user.id
        
        if user_id not in self.admins:
            await update.message.reply_text("❌ Access denied. You are not authorized as an admin.")
            return
            
        await self.show_admin_panel(update, context)
        
    async def show_chat_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /id command - show chat ID for channels and groups"""
        chat = update.effective_chat
        
        # Only work in channels and groups
        if chat.type not in ['channel', 'supergroup', 'group']:
            await update.message.reply_text(
                "❌ **Error**\n\n"
                "This command only works in channels and groups.\n"
                "Use this command in the channel/group where you want to get the ID."
            )
            return
            
        # Check if user is admin in the chat
        try:
            member = await context.bot.get_chat_member(chat.id, update.effective_user.id)
            if member.status not in ['creator', 'administrator']:
                await update.message.reply_text(
                    "❌ **Access Denied**\n\n"
                    "You need to be an admin in this channel/group to use this command."
                )
                return
        except Exception as e:
            await update.message.reply_text(
                "❌ **Error**\n\n"
                "Could not verify your admin status. Make sure the bot has admin rights."
            )
            return
            
        # Show chat information
        chat_type = "Channel" if chat.type == "channel" else "Supergroup" if chat.type == "supergroup" else "Group"
        username_info = f"\n**Username:** @{chat.username}" if chat.username else "\n**Username:** None (Private)"
        
        await update.message.reply_text(
            f"📋 **Chat Information**\n\n"
            f"**Type:** {chat_type}\n"
            f"**Title:** {chat.title}\n"
            f"**ID:** `{chat.id}`\n"
            f"{username_info}\n\n"
            f"**To set as admin group:**\n"
            f"1. Copy the ID: `{chat.id}`\n"
            f"2. Send `/admin` to your bot\n"
            f"3. Click '⚙️ Bot Configuration'\n"
            f"4. Click '📱 Set Admin Group'",
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
            "🔧 **Advanced Admin Panel**\n\n"
            "Welcome to the admin panel. Use the buttons below to configure the bot:",
            reply_markup=reply_markup
        )
        
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline buttons"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = query.from_user.id
        
        # Handle user buttons first (these work for everyone)
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
        
        # Admin-only buttons below
        if user_id not in self.admins:
            await query.edit_message_text("❌ Access denied. You are not authorized as an admin.")
            return
            
        if data == "set_welcome_text":
            self.admin_states[user_id] = "waiting_welcome_text"
            await query.edit_message_text(
                "📝 **Set Welcome Text**\n\n"
                "Send the new welcome message text. This will be displayed with the welcome image."
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
                "Send the URL for the signup button (e.g., https://example.com/signup)"
            )
            
        elif data == "set_join_group_url":
            self.admin_states[user_id] = "waiting_join_group_url"
            await query.edit_message_text(
                "👥 **Set Join Group URL**\n\n"
                "Send the Telegram group/channel invite link (e.g., https://t.me/groupname)"
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
                "Send the URL for the daily bonuses button (e.g., https://example.com/bonuses)"
            )
            
        elif data == "set_admin_group":
            self.admin_states[user_id] = "waiting_admin_group"
            await query.edit_message_text(
                "📱 **Set Admin Group**\n\n"
                "Send the group ID where admin replies should be sent.\n\n"
                "Use /id command in the target group to get the ID."
            )
            
        elif data == "bot_config":
            await self.show_bot_config(query)
            
        elif data == "send_broadcast":
            self.admin_states[user_id] = "waiting_broadcast"
            await query.edit_message_text(
                "📡 **Send Message to All Users**\n\n"
                "Send the message you want to broadcast to all users.\n\n"
                "**Supported formats:**\n"
                "• 📝 Text message\n"
                "• 🖼️ Image with caption\n"
                "• 🎥 Video with caption\n"
                "• 🎵 Audio with caption\n"
                "• 📄 Document with caption\n"
                "• 🎙️ Voice message\n"
                "• 🎭 Sticker\n"
                "• 🎬 GIF/Animation\n\n"
                "Send your message now..."
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
🔧 **Bot Configuration**

📝 **Welcome Text:** {self.bot_config['welcome_text'][:50]}{'...' if len(self.bot_config['welcome_text']) > 50 else ''}
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
        recent_users = sum(1 for user in self.users.values() 
                         if (datetime.now() - datetime.fromisoformat(user["joined_date"])).days <= 7)
        
        await query.edit_message_text(
            f"👥 **User Statistics**\n\n"
            f"📊 **Total Users:** {total_users}\n"
            f"🆕 **New Users (7 days):** {recent_users}\n\n"
            f"**User Breakdown:**\n"
            f"• Users with username: {sum(1 for u in self.users.values() if u.get('username'))}\n"
            f"• Users without username: {sum(1 for u in self.users.values() if not u.get('username'))}\n\n"
            f"**Recent Users:**\n" + 
            "\n".join([f"• @{u['username'] or 'No username'} ({u['first_name']})" 
                       for u in list(self.users.values())[-5:]]) if self.users else "No users yet",
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
                    "📑 **No Logs Available**\n\n"
                    "No activity has been logged yet.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="back_to_admin")
                    ]])
                )
                return
                
            # Show last 10 log entries
            recent_logs = logs[-10:]
            log_text = "📑 **Recent Activity Logs**\n\n" + "".join(recent_logs)
            
            # Truncate if too long
            if len(log_text) > 4000:
                log_text = log_text[:4000] + "\n\n... (truncated)"
                
            await query.edit_message_text(
                log_text,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="back_to_admin")
                ]])
            )
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ **Error Reading Logs**\n\n{str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="back_to_admin")
                ]])
            )
            
    async def stop_bot(self, query):
        """Stop the bot"""
        await query.edit_message_text(
            "🛑 **Bot Stopped**\n\n"
            "The bot has been stopped. You can restart it by running the script again.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="back_to_admin")
            ]])
        )
        
    async def show_admin_panel_from_query(self, query, context):
        """Show admin panel from callback query"""
        await self.show_admin_panel(update=query, context=context)
        
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages for admin responses and live chat"""
        user_id = update.effective_user.id
        message = update.message
        
        # Check if user is waiting for a response (admin)
        if user_id in self.admin_states:
            state = self.admin_states[user_id]
            await self.handle_admin_response(update, context, state)
            return
            
        # Check if user is in live chat mode
        if user_id in self.user_states and self.user_states[user_id] == "live_chat":
            # Check if user wants to exit live chat
            if message.text and message.text.lower() in ['/exit', '/stop', '/quit', 'exit', 'stop', 'quit']:
                del self.user_states[user_id]
                await message.reply_text(
                    "🔙 **Live Chat Ended**\n\n"
                    "😏 **Chat session closed!** See you next time! 👋"
                )
                return
            
            await self.forward_to_admin_group(update, context, user_id)
            return
            
        # Check if this is an admin reply in the admin group
        if str(message.chat.id) == self.bot_config.get("admin_group_id") and message.reply_to_message:
            logger.info(f"Detected admin reply in admin group - calling handle_admin_reply")
            await self.handle_admin_reply(update, context)
            return
            
    async def handle_admin_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE, state: str):
        """Handle admin responses for configuration"""
        message = update.message
        user_id = update.effective_user.id
        
        if state == "waiting_welcome_text":
            self.bot_config["welcome_text"] = message.text
            self.save_welcome()
            await message.reply_text("✅ Welcome text updated successfully!")
            
        elif state == "waiting_welcome_image":
            if message.photo:
                file_id = message.photo[-1].file_id
                self.bot_config["welcome_image"] = file_id
                self.save_bot_config()
                await message.reply_text("✅ Welcome image updated successfully!")
            else:
                await message.reply_text("❌ Please send an image file.")
                return
                
        elif state == "waiting_signup_url":
            if message.text and message.text.startswith(('http://', 'https://')):
                self.bot_config["signup_url"] = message.text
                self.save_bot_config()
                await message.reply_text("✅ Signup URL updated successfully!")
            else:
                await message.reply_text("❌ Please send a valid URL starting with http:// or https://")
                return
                
        elif state == "waiting_join_group_url":
            if message.text and message.text.startswith(('https://t.me/', 'https://telegram.me/')):
                self.bot_config["join_group_url"] = message.text
                self.save_bot_config()
                await message.reply_text("✅ Join group URL updated successfully!")
            else:
                await message.reply_text("❌ Please send a valid Telegram group/channel invite link")
                return
                
        elif state == "waiting_download_apk":
            if message.document:
                file_id = message.document.file_id
                self.bot_config["download_apk"] = file_id
                self.save_bot_config()
                await message.reply_text("✅ Download APK updated successfully!")
            else:
                await message.reply_text("❌ Please send an APK file.")
                return
                
        elif state == "waiting_daily_bonuses":
            if message.text and message.text.startswith(('http://', 'https://')):
                self.bot_config["daily_bonuses_url"] = message.text
                self.save_bot_config()
                await message.reply_text("✅ Daily bonuses URL updated successfully!")
            else:
                await message.reply_text("❌ Please send a valid URL starting with http:// or https://")
                return
                
        elif state == "waiting_admin_group":
            try:
                group_id = int(message.text)
                self.bot_config["admin_group_id"] = str(group_id)
                self.save_bot_config()
                await message.reply_text(f"✅ Admin group ID updated to: {group_id}")
            except ValueError:
                await message.reply_text("❌ Please send a valid group ID (numbers only)")
                return
                
        elif state == "waiting_broadcast":
            await self.broadcast_message_to_all_users(message, context)
            return
            
        # Clear admin state
        if user_id in self.admin_states:
            del self.admin_states[user_id]
            
    async def forward_to_admin_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Forward user message to admin group"""
        if not self.bot_config["admin_group_id"]:
            await update.message.reply_text("❌ Admin group not configured. Please contact admin.")
            return
            
        try:
            user_info = self.users.get(str(user_id), {})
            username = user_info.get('username', 'No username')
            first_name = user_info.get('first_name', 'Unknown')
            
            # Create user info header
            user_header = f"👤 User: @{username} ({first_name})\n🆔 ID: {user_id}\n💬 Message:\n\n"
            
            # Forward the message to admin group
            if update.message.text:
                await context.bot.send_message(
                    chat_id=self.bot_config["admin_group_id"],
                    text=user_header + update.message.text,
                    parse_mode='Markdown'
                )
            elif update.message.photo:
                await context.bot.send_photo(
                    chat_id=self.bot_config["admin_group_id"],
                    photo=update.message.photo[-1].file_id,
                    caption=user_header + (update.message.caption or "📸 Image")
                )
            elif update.message.video:
                await context.bot.send_video(
                    chat_id=self.bot_config["admin_group_id"],
                    video=update.message.video.file_id,
                    caption=user_header + (update.message.caption or "🎥 Video")
                )
            elif update.message.voice:
                await context.bot.send_voice(
                    chat_id=self.bot_config["admin_group_id"],
                    voice=update.message.voice.file_id,
                    caption=user_header + "🎙️ Voice Message"
                )
            elif update.message.audio:
                await context.bot.send_audio(
                    chat_id=self.bot_config["admin_group_id"],
                    audio=update.message.audio.file_id,
                    caption=user_header + (update.message.caption or "🎵 Audio")
                )
            elif update.message.document:
                await context.bot.send_document(
                    chat_id=self.bot_config["admin_group_id"],
                    document=update.message.document.file_id,
                    caption=user_header + (update.message.caption or "📄 Document")
                )
            elif update.message.sticker:
                await context.bot.send_sticker(
                    chat_id=self.bot_config["admin_group_id"],
                    sticker=update.message.sticker.file_id
                )
                await context.bot.send_message(
                    chat_id=self.bot_config["admin_group_id"],
                    text=user_header + "🎭 Sticker"
                )
            elif update.message.animation:
                await context.bot.send_animation(
                    chat_id=self.bot_config["admin_group_id"],
                    animation=update.message.animation.file_id,
                    caption=user_header + (update.message.caption or "🎬 GIF/Animation")
                )
                
            # Confirm to user
            await update.message.reply_text("✅ Your message has been sent to admin. You'll receive a reply soon!")
            
        except Exception as e:
            logger.error(f"Failed to forward message to admin group: {e}")
            await update.message.reply_text("❌ Failed to send message to admin. Please try again later.")
            
    async def handle_admin_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin replies in admin group and forward to user"""
        message = update.message
        
        # Debug logging
        logger.info(f"Admin reply handler called - Chat ID: {message.chat.id}, Admin group ID: {self.bot_config.get('admin_group_id')}")
        
        # Check if this is a reply to a user message
        if not message.reply_to_message:
            logger.info("No reply_to_message - ignoring")
            return
            
        # Check if this is in the admin group
        if str(message.chat.id) != self.bot_config.get("admin_group_id"):
            logger.info(f"Not in admin group - chat ID: {message.chat.id}, expected: {self.bot_config.get('admin_group_id')}")
            return
            
        logger.info("Message is in admin group and is a reply - processing...")
        
        # Extract user ID from the replied message
        reply_text = message.reply_to_message.text or message.reply_to_message.caption or ""
        logger.info(f"Reply text: {reply_text}")
        
        # Look for user ID in the format "🆔 ID: {user_id}"
        import re
        user_id_match = re.search(r'🆔 ID: (\d+)', reply_text)
        
        if not user_id_match:
            logger.info("No user ID found in reply text")
            return
            
        user_id = int(user_id_match.group(1))
        logger.info(f"Extracted user ID: {user_id}")
        
        # Check if user is still in live chat
        if user_id not in self.user_states or self.user_states[user_id] != "live_chat":
            logger.info(f"User {user_id} not in live chat - states: {self.user_states}")
            await message.reply_text("❌ User is no longer in live chat mode.")
            return
            
        logger.info(f"User {user_id} is in live chat - forwarding reply")
        
        try:
            # Forward admin's reply to the user
            if message.text:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"💬 Admin Reply:\n\n{message.text}"
                )
            elif message.photo:
                await context.bot.send_photo(
                    chat_id=user_id,
                    photo=message.photo[-1].file_id,
                    caption=f"💬 Admin Reply:\n\n{message.caption or '📸 Image from admin'}"
                )
            elif message.video:
                await context.bot.send_video(
                    chat_id=user_id,
                    video=message.video.file_id,
                    caption=f"💬 Admin Reply:\n\n{message.caption or '🎥 Video from admin'}"
                )
            elif message.voice:
                await context.bot.send_voice(
                    chat_id=user_id,
                    voice=message.voice.file_id,
                    caption="💬 Admin Reply:\n\n🎙️ Voice message from admin"
                )
            elif message.audio:
                await context.bot.send_audio(
                    chat_id=user_id,
                    audio=message.audio.file_id,
                    caption=f"💬 Admin Reply:\n\n{message.caption or '🎵 Audio from admin'}"
                )
            elif message.document:
                await context.bot.send_document(
                    chat_id=user_id,
                    document=message.document.file_id,
                    caption=f"💬 Admin Reply:\n\n{message.caption or '📄 Document from admin'}"
                )
            elif message.sticker:
                await context.bot.send_sticker(
                    chat_id=user_id,
                    sticker=message.sticker.file_id
                )
                await context.bot.send_message(
                    chat_id=user_id,
                    text="💬 Admin Reply:\n\n🎭 Sticker from admin"
                )
            elif message.animation:
                await context.bot.send_animation(
                    chat_id=user_id,
                    animation=message.animation.file_id,
                    caption=f"💬 Admin Reply:\n\n{message.caption or '🎬 GIF/Animation from admin'}"
                )
                
            # Confirm to admin
            await message.reply_text("✅ Reply sent to user successfully!")
            logger.info(f"Successfully sent admin reply to user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to send admin reply to user {user_id}: {e}")
            await message.reply_text(f"❌ Failed to send reply to user: {e}")
            
    async def exit_live_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /exit command to exit live chat mode"""
        user_id = update.effective_user.id
        
        if user_id in self.user_states and self.user_states[user_id] == "live_chat":
            del self.user_states[user_id]
            await update.message.reply_text(
                "🔙 **Live Chat Ended**\n\n"
                "😏 **Chat session closed!** See you next time! 👋"
            )
        else:
            await update.message.reply_text(
                "ℹ️ **Not in Live Chat**\n\n"
                "😏 **You're not in chat mode!** Use /start to begin the fun! 🚀"
            )
            
    async def broadcast_message_to_all_users(self, message, context):
        """Send message to all users (BROADCAST FEATURE)"""
        if not self.users:
            await message.reply_text("❌ No users found to broadcast to.")
            return

        # Save broadcast message data
        message_data = {}
        if message.text:
            message_data = {"type": "text", "content": message.text}
        elif message.photo:
            message_data = {"type": "photo", "file_id": message.photo[-1].file_id, "caption": message.caption}
        elif message.video:
            message_data = {"type": "video", "file_id": message.video.file_id, "caption": message.caption}
        elif message.voice:
            message_data = {"type": "voice", "file_id": message.voice.file_id, "caption": message.caption}
        elif message.audio:
            message_data = {"type": "audio", "file_id": message.audio.file_id, "caption": message.caption}
        elif message.document:
            message_data = {"type": "document", "file_id": message.document.file_id, "caption": message.caption}
        elif message.video_note:
            message_data = {"type": "video_note", "file_id": message.video_note.file_id}
        elif message.sticker:
            message_data = {"type": "sticker", "file_id": message.sticker.file_id}
        elif message.animation:
            message_data = {"type": "animation", "file_id": message.animation.file_id, "caption": message.caption}
        else:
            await message.reply_text("❌ Unsupported message type for broadcast.")
            return

        # Save broadcast data
        with open(self.broadcast_file, 'w', encoding='utf-8') as f:
            json.dump(message_data, f, indent=2, ensure_ascii=False)

        # Send to all users
        success_count = 0
        failed_count = 0

        await message.reply_text(f"📡 Broadcasting message to {len(self.users)} users...")

        for user_id, user_info in self.users.items():
            # Skip admin users
            if int(user_id) in self.admins:
                continue

            try:
                if message_data["type"] == "text":
                    await context.bot.send_message(
                        chat_id=int(user_id),
                        text=message_data["content"]
                    )
                elif message_data["type"] == "photo":
                    await context.bot.send_photo(
                        chat_id=int(user_id),
                        photo=message_data["file_id"],
                        caption=message_data.get("caption")
                    )
                elif message_data["type"] == "video":
                    await context.bot.send_video(
                        chat_id=int(user_id),
                        video=message_data["file_id"],
                        caption=message_data.get("caption")
                    )
                elif message_data["type"] == "voice":
                    await context.bot.send_voice(
                        chat_id=int(user_id),
                        voice=message_data["file_id"],
                        caption=message_data.get("caption")
                    )
                elif message_data["type"] == "audio":
                    await context.bot.send_audio(
                        chat_id=int(user_id),
                        audio=message_data["file_id"],
                        caption=message_data.get("caption")
                    )
                elif message_data["type"] == "document":
                    await context.bot.send_document(
                        chat_id=int(user_id),
                        document=message_data["file_id"],
                        caption=message_data.get("caption")
                    )
                elif message_data["type"] == "video_note":
                    await context.bot.send_video_note(
                        chat_id=int(user_id),
                        video_note=message_data["file_id"]
                    )
                elif message_data["type"] == "sticker":
                    await context.bot.send_sticker(
                        chat_id=int(user_id),
                        sticker=message_data["file_id"]
                    )
                elif message_data["type"] == "animation":
                    await context.bot.send_animation(
                        chat_id=int(user_id),
                        animation=message_data["file_id"],
                        caption=message_data.get("caption")
                    )

                success_count += 1
                time.sleep(0.1)  # Small delay to avoid rate limiting

            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to send broadcast to user {user_id}: {e}")

        # Send summary
        await message.reply_text(
            f"📡 **Broadcast Complete!**\n\n"
            f"✅ Successfully sent: {success_count}\n"
            f"❌ Failed: {failed_count}\n"
            f"📊 Total users: {len(self.users)}"
        )

        # Log the broadcast
        self.log_broadcast(success_count, failed_count, len(self.users))
        
    def log_broadcast(self, success_count, failed_count, total_users):
        """Log broadcast activity"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] BROADCAST - Success: {success_count}, Failed: {failed_count}, Total: {total_users}\n"
        
        with open(self.LOGS_FILE, 'a') as f:
            f.write(log_entry)
            
    async def handle_join_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle join requests"""
        join_request = update.chat_join_request
        
        try:
            # Approve the join request
            await context.bot.approve_chat_join_request(
                chat_id=join_request.chat.id,
                user_id=join_request.from_user.id
            )
            
            # Send welcome message with image and buttons
            await self.send_welcome_message(context.bot, join_request.from_user.id)
            self.log_join(join_request.from_user.username, join_request.from_user.id, True)
            
        except Exception as e:
            logger.error(f"Error handling join request: {e}")
            self.log_join(join_request.from_user.username, join_request.from_user.id, False, str(e))
            
    async def send_welcome_message(self, bot, user_id: int):
        """Send welcome message with image and buttons"""
        try:
            # Create inline keyboard - each button on its own row (full width)
            keyboard = []
            
            if self.bot_config["signup_url"]:
                keyboard.append([InlineKeyboardButton("🔑 Signup", url=self.bot_config["signup_url"])])
                
            if self.bot_config["join_group_url"]:
                keyboard.append([InlineKeyboardButton("📢 Join Group", url=self.bot_config["join_group_url"])])
                
            keyboard.append([InlineKeyboardButton("💬 Live Chat", callback_data="live_chat")])
            
            if self.bot_config["download_apk"]:
                keyboard.append([InlineKeyboardButton("📥 Download Hack", callback_data="download_hack")])
                
            if self.bot_config["daily_bonuses_url"]:
                keyboard.append([InlineKeyboardButton("🎁 Daily Bonuses", url=self.bot_config["daily_bonuses_url"])])
                
            reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
            
            # Send welcome message
            if self.bot_config["welcome_image"]:
                await bot.send_photo(
                    chat_id=user_id,
                    photo=self.bot_config["welcome_image"],
                    caption=self.bot_config["welcome_text"],
                    reply_markup=reply_markup
                )
            else:
                await bot.send_message(
                    chat_id=user_id,
                    text=self.bot_config["welcome_text"],
                    reply_markup=reply_markup
                )
                
        except Exception as e:
            logger.error(f"Failed to send welcome message: {e}")
            # Fallback to text-only message
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=self.bot_config["welcome_text"]
                )
            except Exception as e2:
                logger.error(f"Failed to send fallback welcome message: {e2}")
                
    # Button handlers
    async def handle_signup(self, query, context):
        """Handle signup button click"""
        if self.bot_config["signup_url"]:
            await query.answer("🔑 **Time to level up!** 🚀")
            # The button already has the URL, so no action needed
        else:
            await query.answer("❌ Signup URL not configured yet!", show_alert=True)
            
    async def handle_join_group(self, query, context):
        """Handle join group button click"""
        if self.bot_config["join_group_url"]:
            await query.answer("📢 **Join the elite squad!** 💪")
            # The button already has the URL, so no action needed
        else:
            await query.answer("❌ Join group URL not configured yet!", show_alert=True)
            
    async def start_live_chat(self, query, context):
        """Start live chat with user"""
        user_id = query.from_user.id
        
        try:
            # Check if admin group is configured
            if not self.bot_config["admin_group_id"]:
                await query.answer("❌ Admin group not configured yet!", show_alert=True)
                return
            
            # Set user state to live chat
            self.user_states[user_id] = "live_chat"
            
            # Send simple, direct message with exit button
            keyboard = [
                [InlineKeyboardButton("🔙 Exit Live Chat", callback_data="exit_live_chat")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await context.bot.send_message(
                chat_id=user_id,
                text="💬 **You are now connected to live chat with Admin**\n\n"
                     "🔥 **Ready to chat with the boss?** 🔥\n\n"
                     "Send any message and it will be forwarded to admin.\n\n"
                     "Use the button below or type /exit to stop live chat.",
                reply_markup=reply_markup
            )
            
            # Answer callback query
            await query.answer("✅ Live chat connected!")
            
        except Exception as e:
            logger.error(f"Error starting live chat: {e}")
            await query.answer("❌ Failed to start live chat", show_alert=True)
            
    async def exit_live_chat_from_button(self, query, context):
        """Handle exit live chat button click"""
        user_id = query.from_user.id
        
        if user_id in self.user_states and self.user_states[user_id] == "live_chat":
            del self.user_states[user_id]
            
            # Edit the message to show exit confirmation
            keyboard = [
                [InlineKeyboardButton("🚀 Start New Chat", callback_data="start_live_chat")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "🔙 **Live Chat Ended**\n\n"
                "😏 **Chat session closed!** See you next time! 👋\n\n"
                "Want to chat again?",
                reply_markup=reply_markup
            )
            
            await query.answer("🔙 Live chat exited!")
        else:
            await query.answer("ℹ️ You're not in live chat mode!", show_alert=True)
            
    async def handle_download_hack(self, query, context):
        """Handle download hack button click"""
        try:
            if self.bot_config["download_apk"]:
                # Send APK file with teasing caption
                await context.bot.send_document(
                    chat_id=query.from_user.id,
                    document=self.bot_config["download_apk"],
                    caption="🎯 **Here's Your Premium APK!** 🎯\n\n🔥 **Enjoy the power!** 🔥"
                )

                # Answer callback query
                await query.answer("🎯 Premium APK delivered! Enjoy! 🚀")

            else:
                await query.answer("❌ Download APK not configured yet!", show_alert=True)

        except Exception as e:
            logger.error(f"Failed to send APK: {e}")
            await query.answer("❌ Failed to send APK", show_alert=True)
            
    async def handle_daily_bonuses(self, query, context):
        """Handle daily bonuses button click"""
        if self.bot_config["daily_bonuses_url"]:
            await query.answer("🎁 **Claim your rewards!** ⭐")
            # The button already has the URL, so no action needed
        else:
            await query.answer("❌ Daily bonuses URL not configured yet!", show_alert=True)
            
    def run(self):
        """Run the bot"""
        print("🚀 Starting Advanced Bot...")
        self.application.run_polling()

def main():
    """Main function"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ Error: TELEGRAM_BOT_TOKEN environment variable not set!")
        print("Please set your bot token:")
        print("export TELEGRAM_BOT_TOKEN='your_bot_token_here'")
        return
        
    bot = AdvancedTelegramBot(token)
    bot.run()

if __name__ == "__main__":
    main()
