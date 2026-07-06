from telegram import Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
)

from database.admins import is_admin
from database.users import users_collection


async def broadcast(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text(
            "❌ You are not authorized."
        )
        return

    if not context.args:
        await update.message.reply_text(
            "Usage:\n/broadcast Your message"
        )
        return

    message = " ".join(context.args)

    users = await users_collection().find().to_list(length=None)

    success = 0
    failed = 0

    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user["user_id"],
                text=message,
            )
            success += 1
        except Exception:
            failed += 1

    await update.message.reply_text(
        f"✅ Broadcast completed.\n\n"
        f"Success: {success}\n"
        f"Failed: {failed}"
    )


def broadcast_handler():
    return CommandHandler(
        "broadcast",
        broadcast,
    )
