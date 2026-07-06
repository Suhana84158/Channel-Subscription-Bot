from telegram import Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
)

from database.users import get_or_create_user


WELCOME_MESSAGE = """
👋 Welcome to the Subscription Bot!

✨ Available Features:

• Subscription Plans
• Secure UPI Payment
• Auto Channel Access
• Auto Renewal
• Referral Rewards

Use the menu below to continue.
"""


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user

    await get_or_create_user(user)

    await update.message.reply_text(
        WELCOME_MESSAGE
    )


def start_command():
    return CommandHandler(
        "start",
        start,
    )
