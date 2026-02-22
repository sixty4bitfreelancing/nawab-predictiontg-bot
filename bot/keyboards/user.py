"""User-facing keyboards."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def live_chat_exit_keyboard() -> InlineKeyboardMarkup:
    """Exit live chat button."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Exit Live Chat", callback_data="exit_live_chat")]
    ])


def live_chat_start_keyboard() -> InlineKeyboardMarkup:
    """Start new chat button (after exit)."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Start New Chat", callback_data="live_chat")]
    ])
