"""Start command handler."""

from telegram import Update
from telegram.ext import ContextTypes

from bot.services.user_service import is_admin, upsert_user
from bot.services.welcome_service import send_welcome
from bot.utils.maintenance import check_maintenance
from bot.utils.logger import get_logger

logger = get_logger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    if await check_maintenance(update, context):
        return
    user = update.effective_user
    if not user:
        return

    # Register user (skip admins in user list for stats)
    is_adm = await is_admin(user.id)
    if not is_adm:
        await upsert_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
        )

    await send_welcome(context.bot, user.id)
