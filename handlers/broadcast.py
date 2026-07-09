from telegram import Update
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from database.admins import is_admin
from database.users import users_collection

WAIT_BROADCAST = 1


async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized.")
        return ConversationHandler.END

    await update.message.reply_text(
        "📢 Send the message you want to broadcast.\n\n"
        "You can send text, photo, video, document, or forward any message."
    )

    return WAIT_BROADCAST


async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id):
        return ConversationHandler.END

    users = await users_collection().find().to_list(length=None)

    success = 0
    failed = 0

    progress = await update.message.reply_text(
        f"📢 Broadcast started...\n\nTotal users: {len(users)}"
    )

    for user in users:
        try:
            await context.bot.copy_message(
                chat_id=user["user_id"],
                from_chat_id=update.message.chat_id,
                message_id=update.message.message_id,
            )
            success += 1
        except Exception:
            failed += 1

    await progress.edit_text(
        f"✅ Broadcast completed.\n\n"
        f"👥 Total Users: {len(users)}\n"
        f"✅ Sent: {success}\n"
        f"❌ Failed: {failed}"
    )

    return ConversationHandler.END


def broadcast_handler():
    return ConversationHandler(
        entry_points=[
            CommandHandler("broadcast", broadcast_start),
        ],
        states={
            WAIT_BROADCAST: [
                MessageHandler(filters.ALL, send_broadcast),
            ]
        },
        fallbacks=[],
    )
