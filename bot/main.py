"""
Bot v2 - Production-grade modular Telegram bot.
Entry point. Registers global error handler and all handlers.
"""

import sys

from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ChatJoinRequestHandler,
    filters,
)

from bot.config import TELEGRAM_BOT_TOKEN, SUPERADMIN_ID
from bot.database import init_db, close_pool
from bot.utils.error_handler import global_error_handler
from bot.utils.logger import get_logger

from bot.handlers.start import start_command
from bot.handlers.admin import admin_command, show_chat_id_command
from bot.handlers.callbacks import handle_callback
from bot.handlers.messages import handle_message
from bot.handlers.join import handle_join_request
from bot.handlers.exit_cmd import exit_live_chat_command

logger = get_logger(__name__)

MESSAGE_FILTER = (
    filters.TEXT
    | filters.VOICE
    | filters.PHOTO
    | filters.VIDEO
    | filters.Document.ALL
    | filters.AUDIO
    | filters.VIDEO_NOTE
    | filters.Sticker.ALL
    | filters.ANIMATION
) & ~filters.COMMAND


def build_application() -> Application:
    """Build and configure the Application."""
    if not TELEGRAM_BOT_TOKEN:
        logger.critical("TELEGRAM_BOT_TOKEN is not set")
        sys.exit(1)

    application = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # CRITICAL: Global error handler - must be registered first
    application.add_error_handler(global_error_handler)

    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("id", show_chat_id_command))
    application.add_handler(CommandHandler("exit", exit_live_chat_command))

    # Callback handler
    application.add_handler(CallbackQueryHandler(handle_callback))

    # Message handler
    application.add_handler(MessageHandler(MESSAGE_FILTER, handle_message))

    # Join request handler
    application.add_handler(ChatJoinRequestHandler(handle_join_request))

    return application


async def post_init(application: Application) -> None:
    """Run after application is initialized (before polling)."""
    await init_db()
    # Optionally add superadmin
    if SUPERADMIN_ID:
        from bot.services.user_service import add_admin
        await add_admin(SUPERADMIN_ID)
        logger.info("Superadmin %s added", SUPERADMIN_ID)


async def post_shutdown(application: Application) -> None:
    """Run after application stops."""
    await close_pool()


def main() -> None:
    """Main entry point."""
    application = build_application()
    logger.info("Starting Bot v2...")
    application.run_polling(
        allowed_updates=Application.ALL_UPDATES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
