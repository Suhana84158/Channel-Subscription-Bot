from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from database.admins import get_all_admins

WAIT_SUPPORT = 1


async def support_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "📞 *Support*\n\n"
        "Please type your issue here.\n\n"
        "Your message will be sent to admin.",
        parse_mode="Markdown",
    )

    return WAIT_SUPPORT


async def receive_support_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message_text = update.message.text

    admins = await get_all_admins()

    text = (
        "📞 New Support Request\n\n"
        f"👤 User: {user.first_name}\n"
        f"🆔 User ID: `{user.id}`\n"
        f"📛 Username: @{user.username if user.username else 'None'}\n\n"
        f"💬 Message:\n{message_text}"
    )

    for admin in admins:
        try:
            await context.bot.send_message(
                chat_id=admin["admin_id"],
                text=text,
                parse_mode="Markdown",
            )
        except:
            pass

    await update.message.reply_text(
        "✅ Your support request has been sent to admin."
    )

    return ConversationHandler.END


def support_callback():
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                support_handler,
                pattern="^support$",
            )
        ],
        states={
            WAIT_SUPPORT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    receive_support_message,
                )
            ]
        },
        fallbacks=[],
    )
