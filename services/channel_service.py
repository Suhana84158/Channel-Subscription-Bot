from telegram import Bot
from telegram.error import TelegramError

from config import BOT_TOKEN
from database.channels import get_all_channels
from logging_config import get_logger

logger = get_logger(__name__)

bot = Bot(token=BOT_TOKEN)


async def grant_channel_access(user_id: int):
    """
    Generate one-time invite links for all premium channels.
    """

    channels = await get_all_channels()

    for channel in channels:
        try:
            invite = await bot.create_chat_invite_link(
                chat_id=channel["chat_id"],
                member_limit=1,
            )

            await bot.send_message(
                chat_id=user_id,
                text=(
                    f"🎉 Access Granted\n\n"
                    f"📢 {channel['title']}\n\n"
                    f"{invite.invite_link}"
                ),
            )

        except TelegramError as e:
            logger.exception(
                f"Failed to create invite for {channel['chat_id']}: {e}"
            )


async def revoke_channel_access(user_id: int):
    """
    Remove expired user from all premium channels.
    """

    channels = await get_all_channels()

    for channel in channels:
        try:
            await bot.ban_chat_member(
                chat_id=channel["chat_id"],
                user_id=user_id,
            )

            await bot.unban_chat_member(
                chat_id=channel["chat_id"],
                user_id=user_id,
            )

        except TelegramError as e:
            logger.exception(
                f"Failed removing {user_id} from {channel['chat_id']}: {e}"
            )
