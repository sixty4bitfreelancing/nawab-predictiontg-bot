"""Join request handler - auto-approve and send welcome."""

from telegram import Update
from telegram.ext import ContextTypes

from bot.services.welcome_service import send_welcome
from bot.services.log_service import log_join
from bot.services.user_service import upsert_user
from bot.utils.exceptions import WelcomeBuilderError
from bot.utils.logger import get_logger

logger = get_logger(__name__)


async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Auto-approve join request and send welcome message."""
    join_req = update.chat_join_request
    if not join_req:
        return

    user = join_req.from_user
    user_id = user.id
    username = user.username

    try:
        await context.bot.approve_chat_join_request(
            chat_id=join_req.chat.id,
            user_id=user_id,
        )
    except Exception as e:
        logger.exception("Failed to approve join request for %s: %s", user_id, e)
        await log_join(user_id, username, False, str(e))
        return

    await upsert_user(
        user_id=user_id,
        username=username,
        first_name=user.first_name,
        last_name=user.last_name,
    )

    try:
        await send_welcome(context.bot, user_id)
        await log_join(user_id, username, True, None)
    except WelcomeBuilderError as e:
        logger.exception("Failed to send welcome to %s: %s", user_id, e)
        await log_join(user_id, username, False, str(e))
