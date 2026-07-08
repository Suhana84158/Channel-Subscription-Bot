from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from database.admins import is_admin, add_admin, remove_admin
from database.channels import add_channel, remove_channel, get_all_channels


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized.")
        return

    keyboard = [
        [InlineKeyboardButton("➕ Add Channel/Group", callback_data="admin_add_channel")],
        [InlineKeyboardButton("📋 Channel List", callback_data="admin_list_channels")],
        [InlineKeyboardButton("❌ Remove Channel", callback_data="admin_remove_help")],
    ]

    await update.message.reply_text(
        "🛠 Admin Panel\n\nChoose an option:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def admin_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not await is_admin(query.from_user.id):
        await query.edit_message_text("❌ Not authorized.")
        return

    if query.data == "admin_add_channel":
        context.user_data["waiting_channel_forward"] = True
        await query.edit_message_text(
            "📢 Forward any message from your channel/group here.\n\n"
            "⚠️ Bot must be admin in that channel/group."
        )

    elif query.data == "admin_list_channels":
        channels = await get_all_channels()

        if not channels:
            await query.edit_message_text("No channel/group added yet.")
            return

        text = "📋 Added Channels/Groups:\n\n"

        for channel in channels:
            text += (
                f"• {channel.get('title', 'Unknown')}\n"
                f"ID: `{channel.get('chat_id')}`\n\n"
            )

        await query.edit_message_text(text, parse_mode="Markdown")

    elif query.data == "admin_remove_help":
        await query.edit_message_text(
            "Use this command:\n\n"
            "`/removechannel CHAT_ID`\n\n"
            "Example:\n"
            "`/removechannel -1001234567890`",
            parse_mode="Markdown",
        )


async def handle_forwarded_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id):
        return

    if not context.user_data.get("waiting_channel_forward"):
        return

    message = update.message
    chat = None

    if message.forward_from_chat:
        chat = message.forward_from_chat

    if not chat and message.forward_origin:
        origin = message.forward_origin
        if hasattr(origin, "chat"):
            chat = origin.chat

    if not chat:
        await message.reply_text(
            "❌ Channel/group detect nahi hua.\n\n"
            "Please forward message directly from channel/group."
        )
        return

    await add_channel(chat.id, chat.title or "Unknown")

    context.user_data["waiting_channel_forward"] = False

    await message.reply_text(
        f"✅ Channel/Group added successfully!\n\n"
        f"Title: {chat.title}\n"
        f"ID: `{chat.id}`",
        parse_mode="Markdown",
    )


async def add_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized.")
        return

    context.user_data["waiting_channel_forward"] = True

    await update.message.reply_text(
        "📢 Forward any message from your channel/group here.\n\n"
        "⚠️ Bot must be admin in that channel/group."
    )


async def remove_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized.")
        return

    if len(context.args) != 1:
        await update.message.reply_text(
            "Usage:\n/removechannel CHAT_ID"
        )
        return

    await remove_channel(int(context.args[0]))

    await update.message.reply_text("✅ Channel/Group removed successfully.")


async def add_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage:\n/addadmin USER_ID")
        return

    await add_admin(int(context.args[0]))

    await update.message.reply_text("✅ Admin added successfully.")


async def remove_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage:\n/removeadmin USER_ID")
        return

    await remove_admin(int(context.args[0]))

    await update.message.reply_text("✅ Admin removed successfully.")


def admin_handlers():
    return [
        CommandHandler("admin", admin_panel),
        CommandHandler("addchannel", add_channel_command),
        CommandHandler("removechannel", remove_channel_command),
        CommandHandler("addadmin", add_admin_command),
        CommandHandler("removeadmin", remove_admin_command),
        CallbackQueryHandler(admin_button, pattern=r"^admin_"),
        MessageHandler(filters.FORWARDED, handle_forwarded_channel),
    ]
