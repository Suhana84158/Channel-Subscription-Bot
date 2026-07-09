from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes


async def support_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "📞 *Support*\n\n"
        "If you need help, contact admin.\n\n"
        "Send your issue here or message the bot owner.",
        parse_mode="Markdown",
    )


def support_callback():
    return CallbackQueryHandler(
        support_handler,
        pattern="^support$",
    )
