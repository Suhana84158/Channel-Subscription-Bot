from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from database.users import get_or_create_user
from keyboards.main_menu import get_main_menu


WELCOME_MESSAGE = """
👋 *Welcome to Subscription Bot!*

Choose an option from the menu below.

✨ Features:
• Premium Channel Access
• Secure UPI Payment
• Auto Subscription
• Referral Rewards
• Fast Support
"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_user = update.effective_user

    user = await get_or_create_user(tg_user)

    if user.get("banned"):
        await update.message.reply_text(
            "🚫 You are banned from using this bot.\n\n"
            "If you think this is a mistake, contact admin."
        )
        return

    await update.message.reply_text(
        text=WELCOME_MESSAGE,
        reply_markup=get_main_menu(),
        parse_mode="Markdown",
    )


def start_command():
    return CommandHandler("start", start)
