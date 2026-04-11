"""Admin panel keyboards."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def admin_panel_keyboard() -> InlineKeyboardMarkup:
    """Main admin panel keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("📝 Set Welcome Text", callback_data="set_welcome_text"),
            InlineKeyboardButton("🖼️ Set Welcome Image", callback_data="set_welcome_image"),
        ],
        [
            InlineKeyboardButton("👁 Preview Welcome Message", callback_data="preview_welcome"),
        ],
        [
            InlineKeyboardButton("🔘 Custom Welcome Buttons (max 10)", callback_data="custom_welcome_buttons"),
        ],
        [
            InlineKeyboardButton("⚙️ Bot Configuration", callback_data="bot_config"),
        ],
        [
            InlineKeyboardButton("📡 Send Message to All Users", callback_data="send_broadcast"),
            InlineKeyboardButton("📡 Broadcast Status", callback_data="broadcast:status"),
        ],
        [
            InlineKeyboardButton("👥 View User Stats", callback_data="view_users"),
        ],
        [
            InlineKeyboardButton("🔄 Toggle Auto-Accept Join", callback_data="toggle_auto_accept"),
        ],
        [
            InlineKeyboardButton("📑 View Logs", callback_data="view_logs"),
            InlineKeyboardButton("🛑 Stop Bot", callback_data="stop_bot"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def back_to_admin_keyboard() -> InlineKeyboardMarkup:
    """Back to admin panel button."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="back_to_admin")]
    ])


def confirm_broadcast_keyboard() -> InlineKeyboardMarkup:
    """Confirm or cancel before sending a broadcast (Ram-style)."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Send", callback_data="broadcast:confirm"),
            InlineKeyboardButton("❌ Cancel", callback_data="broadcast:cancel"),
        ],
    ])


def broadcast_wait_keyboard() -> InlineKeyboardMarkup:
    """While waiting for the broadcast message — same feel as Ram (Cancel + Back)."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel", callback_data="broadcast:cancel")],
        [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="back_to_admin")],
    ])
