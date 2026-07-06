from telegram import Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
)

from database.admins import (
    is_admin,
    add_admin,
    remove_admin,
)
from database.channels import (
    add_channel,
    remove_channel,
)


async def admin_panel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text(
            "❌ You are not authorized."
        )
        return

    text = (
        "🛠 *Admin Panel*\n\n"
        "/addadmin <user_id>\n"
        "/removeadmin <user_id>\n"
        "/addchannel <chat_id>\n"
        "/removechannel <chat_id>\n"
        "/broadcast\n"
        "/stats"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
    )


async def add_admin_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await is_admin(update.effective_user.id):
        return

    if len(context.args) != 1:
        await update.message.reply_text(
            "Usage:\n/addadmin USER_ID"
        )
        return

    user_id = int(context.args[0])

    await add_admin(user_id)

    await update.message.reply_text(
        "✅ Admin added successfully."
    )


async def remove_admin_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await is_admin(update.effective_user.id):
        return

    if len(context.args) != 1:
        await update.message.reply_text(
            "Usage:\n/removeadmin USER_ID"
        )
        return

    user_id = int(context.args[0])

    await remove_admin(user_id)

    await update.message.reply_text(
        "✅ Admin removed successfully."
    )


async def add_channel_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await is_admin(update.effective_user.id):
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage:\n/addchannel CHAT_ID TITLE"
        )
        return

    chat_id = int(context.args[0])
    title = " ".join(context.args[1:])

    await add_channel(chat_id, title)

    await update.message.reply_text(
        "✅ Channel added successfully."
    )


async def remove_channel_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await is_admin(update.effective_user.id):
        return

    if len(context.args) != 1:
        await update.message.reply_text(
            "Usage:\n/removechannel CHAT_ID"
        )
        return

    chat_id = int(context.args[0])

    await remove_channel(chat_id)

    await update.message.reply_text(
        "✅ Channel removed successfully."
    )


def admin_handlers():
    return [
        CommandHandler("admin", admin_panel),
        CommandHandler("addadmin", add_admin_command),
        CommandHandler("removeadmin", remove_admin_command),
        CommandHandler("addchannel", add_channel_command),
        CommandHandler("removechannel", remove_channel_command),
    ]
