from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from database.admins import is_admin, add_admin, remove_admin
from database.channels import add_channel, remove_channel, get_all_channels, total_channels
from database.users import total_users
from database.payments import total_revenue

WAIT_CHANNEL = 1


def admin_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Channel/Group", callback_data="admin_add_channel")],
        [InlineKeyboardButton("📋 Channel List", callback_data="admin_channels")],
        [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")],
        [InlineKeyboardButton("👮 Admin Commands", callback_data="admin_commands")],
    ])


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized.")
        return

    await update.message.reply_text(
        "🛠 Admin Panel\n\nChoose an option:",
        reply_markup=admin_keyboard(),
    )


async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not await is_admin(query.from_user.id):
        await query.edit_message_text("❌ You are not authorized.")
        return

    if query.data == "admin_add_channel":
        context.user_data["waiting_channel"] = True
        await query.edit_message_text(
            "📢 Forward any message from your channel/group.\n\n"
            "⚠ Bot must be admin there."
        )

    elif query.data == "admin_channels":
        channels = await get_all_channels()

        if not channels:
            await query.edit_message_text(
                "📋 No channel/group added yet.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅ Back", callback_data="admin_back")]
                ]),
            )
            return

        keyboard = []
        text = "📋 Added Channels/Groups:\n\n"

        for channel in channels:
            chat_id = channel.get("chat_id")
            title = channel.get("title", "Unknown")

            text += f"• {title}\nID: {chat_id}\n\n"
            keyboard.append([
                InlineKeyboardButton(
                    f"❌ Remove {title}",
                    callback_data=f"admin_remove_{chat_id}",
                )
            ])

        keyboard.append([InlineKeyboardButton("⬅ Back", callback_data="admin_back")])

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data.startswith("admin_remove_"):
        chat_id = int(query.data.replace("admin_remove_", ""))
        await remove_channel(chat_id)

        await query.edit_message_text(
            "✅ Channel/Group removed successfully.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅ Back", callback_data="admin_back")]
            ]),
        )

    elif query.data == "admin_stats":
        users = await total_users()
        channels = await total_channels()
        revenue = await total_revenue()

        await query.edit_message_text(
            f"📊 Bot Statistics\n\n"
            f"👤 Users: {users}\n"
            f"📢 Channels: {channels}\n"
            f"💰 Revenue: ₹{revenue}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅ Back", callback_data="admin_back")]
            ]),
        )

    elif query.data == "admin_commands":
        await query.edit_message_text(
            "👮 Admin Commands\n\n"
            "/addadmin USER_ID\n"
            "/removeadmin USER_ID\n"
            "/addchannel\n"
            "/removechannel CHAT_ID\n"
            "/stats",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅ Back", callback_data="admin_back")]
            ]),
        )

    elif query.data == "admin_back":
        await query.edit_message_text(
            "🛠 Admin Panel\n\nChoose an option:",
            reply_markup=admin_keyboard(),
        )


async def add_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized.")
        return

    context.user_data["waiting_channel"] = True

    await update.message.reply_text(
        "📢 Forward any message from your channel/group.\n\n"
        "⚠ Bot must be admin there."
    )


async def receive_channel_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id):
        return

    if not context.user_data.get("waiting_channel"):
        return

    message = update.message
    chat = getattr(message, "forward_from_chat", None)

    if chat is None:
        origin = getattr(message, "forward_origin", None)
        chat = getattr(origin, "chat", None)

    if chat is None:
        await message.reply_text(
            "❌ Channel/group detect nahi hua.\n\n"
            "Please channel/group se message forward karo."
        )
        return

    await add_channel(chat_id=chat.id, title=chat.title or "Unknown")

    context.user_data["waiting_channel"] = False

    await message.reply_text(
        f"✅ Channel/Group added successfully!\n\n"
        f"Title: {chat.title}\n"
        f"ID: {chat.id}"
    )


async def remove_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage:\n/removechannel CHAT_ID")
        return

    await remove_channel(int(context.args[0]))
    await update.message.reply_text("✅ Channel removed successfully.")


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


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized.")
        return

    users = await total_users()
    channels = await total_channels()
    revenue = await total_revenue()

    await update.message.reply_text(
        f"📊 Bot Statistics\n\n"
        f"👤 Users: {users}\n"
        f"📢 Channels: {channels}\n"
        f"💰 Revenue: ₹{revenue}"
    )


def admin_handlers():
    return [
        CommandHandler("admin", admin_panel),
        CommandHandler("stats", stats_command),
        CommandHandler("addadmin", add_admin_command),
        CommandHandler("removeadmin", remove_admin_command),
        CommandHandler("addchannel", add_channel_start),
        CommandHandler("removechannel", remove_channel_command),
        CallbackQueryHandler(admin_buttons, pattern=r"^admin_"),
        MessageHandler(filters.FORWARDED, receive_channel_forward),
    ]
