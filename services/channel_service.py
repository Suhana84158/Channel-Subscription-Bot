from telegram import Bot

from config import BOT_TOKEN
from database.channels import get_all_channels

from logging_config import get_logger

logger = get_logger(__name__)

bot = Bot(BOT_TOKEN)


# -------------------------
# GRANT ACCESS
# -------------------------
async def grant_channel_access(user_id: int):
    """
    Add user to all premium channels
    after successful payment
    """

    channels = await get_all_channels()

    for channel in channels:
        try:
            invite_link = await bot.create_chat_invite_link(
                chat_id=channel["chat_id"],
                member_limit=1,
                creates_join_request=False,
            )

            await bot.send_message(
                chat_id=user_id,
                text=(
                    f"🎉 You got access to: {channel['title']}\n\n"
                    f"🔗 Join here:\n{invite_link.invite_link}"
                ),
            )

        except Exception as e:
            logger.exception(e)


# -------------------------
# REVOKE ACCESS
# -------------------------
async def revoke_channel_access(user_id: int):
    """
    Remove user from all channels after expiry
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

        except Exception as e:
            logger.exception(e)
