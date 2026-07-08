from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

from database.admins import is_admin, add_admin, remove_admin
from database.channels import add_channel, remove_channel, get_all_channels


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized.")
        return

    keyboard = [
        [InlineKeyboardButton("➕ Add Channel/Group", callback_data="admin_add_channel")],
        [InlineKeyboardButton("📋 Channels List", callback_data="admin_list_channels")],
        [InlineKeyboardButton("❌ Remove Channel", callback_data="admin_remove_help")],
    ]

    await update.message.reply_text(
        "🛠 Admin Panel\n\n"
        "Choose option below:",
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
            "Or use command:\n"
            "/addchannel CHAT_ID TITLE\n\n"
            "Example:\n"
            "/addchannel -1001234567890 Premium Channel"
        )

    elif query.data == "admin_list_channels":
        channels = await get_all_channels()

        if not channels:
            await query.edit_message_text("No channels added yet.")
            return

        text = "📋 Added Channels/Groups:\n\n"
        for ch in channels:
            text += f"• {ch.get('title', 'No Title')}\nID: `{ch.get('chat_id')}`\n\n"

        await query.edit_message_text(text, parse_mode="Markdown")

    elif query.data == "admin_remove_help":
        await query.edit_message_text(
            "To remove channel/group use:\n\n"
            "/removechannel CHAT_ID\n\n"
            "Example:\n"
            "/removechannel -1001234567890"
        )


async def handle_channel_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id):
        return

    if not context.user_data.get("waiting_channel_forward"):
        return

    message = update.message
    chat = None

    if getattr(message, "forward_from_chat", None):
        chat = message.forward_from_chat

    if not chat and getattr(message, "forward_origin", None):
        origin = message.forward_origin
        if getattr(origin, "chat", None):
            chat = origin.chat

    if not chat:
        await message.reply_text(
            "❌ Channel/group detect nahi hua.\n\n"
            "Manual command use karo:\n"
            "/addchannel CHAT_ID TITLE"
        )
        return

    await add_channel(chat.id, chat.title or "Unknown")

    context.user_data["waiting_channel_forward"] = False

    await message.reply_text(
        f"✅ Channel/Group added successfully.\n\n"
        f"Title: {chat.title}\n"
        f"ID: `{chat.id}`",
        parse_mode="Markdown",
    )


async def add_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id):
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage:\n/addadmin USER_ID")
        return

    await add_admin(int(context.args[0]))
    await update.message.reply_text("✅ Admin added successfully.")


async def remove_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id):
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage:\n/removeadmin USER_ID")
        return

    await remove_admin(int(context.args[0]))
    await update.message.reply_text("✅ Admin removed successfully.")


async def add_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id):
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage:\n/addchannel CHAT_ID TITLE")
        return

    chat_id = int(context.args[0])
    title = " ".join(context.args[1:])

    await add_channel(chat_id, title)
    await update.message.reply_text("✅ Channel/Group added successfully.")


async def remove_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id):
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage:\n/removechannel CHAT_ID")
        return

    await remove_channel(int(context.args[0]))
    await update.message.reply_text("✅ Channel/Group removed successfully.")


def admin_handlers():
    return [
        CommandHandler("admin", admin_panel),
        CommandHandler("addadmin", add_admin_command),
        CommandHandler("removeadmin", remove_admin_command),
        CommandHandler("addchannel", add_channel_command),
        CommandHandler("removechannel", remove_channel_command),
        CallbackQueryHandler(admin_button, pattern=r"^admin_"),
        MessageHandler(filters.FORWARDED, handle_channel_forward),
    ]
