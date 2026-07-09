from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from config import ADMIN_IDS
from database.admins import get_all_admins

WAIT_SUPPORT = 1


async def support_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "📞 Support\n\n"
        "Please type your issue here.\n\n"
        "Your message will be sent to admin."
    )

    return WAIT_SUPPORT


async def receive_support_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message_text = update.message.text

    admin_ids = set(ADMIN_IDS)

    try:
        admins = await get_all_admins()
        for admin in admins:
            admin_id = admin.get("admin_id") or admin.get("user_id")
            if admin_id:
                admin_ids.add(int(admin_id))
    except Exception:
        pass

    text = (
        "📞 New Support Request\n\n"
        f"👤 User: {user.first_name}\n"
        f"🆔 User ID: {user.id}\n"
        f"📛 Username: @{user.username if user.username else 'None'}\n\n"
        f"💬 Message:\n{message_text}"
    )

    sent = 0

    for admin_id in admin_ids:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=text,
            )
            sent += 1
        except Exception as e:
            print(f"Support message send failed to {admin_id}: {e}")

    if sent > 0:
        await update.message.reply_text(
            "✅ Your support request has been sent to admin."
        )
    else:
        await update.message.reply_text(
            "❌ Support message send nahi hua. Admin ID check karo."
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
