from telegram import Update
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

from database.admins import is_admin, add_admin, remove_admin
from database.channels import add_channel, remove_channel, get_all_channels, total_channels
from database.users import total_users
from database.payments import total_revenue


WAIT_CHANNEL = 1


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized.")
        return

    text = (
        "🛠 Admin Panel\n\n"
        "/addadmin <user_id>\n"
        "/removeadmin <user_id>\n"
        "/addchannel\n"
        "/removechannel <chat_id>\n"
        "/stats"
    )

    await update.message.reply_text(text)


async def add_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized.")
        return ConversationHandler.END

    await update.message.reply_text(
        "📢 Forward any message from your channel/group.\n\n"
        "⚠ Bot must be admin there."
    )

    return WAIT_CHANNEL


async def receive_channel_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id):
        return ConversationHandler.END

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
        return WAIT_CHANNEL

    await add_channel(chat_id=chat.id, title=chat.title or "Unknown")

    await message.reply_text(
        f"✅ Channel/Group added successfully!\n\n"
        f"Title: {chat.title}\n"
        f"ID: `{chat.id}`",
        parse_mode="Markdown",
    )

    return ConversationHandler.END


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
        CommandHandler("removechannel", remove_channel_command),

        ConversationHandler(
            entry_points=[CommandHandler("addchannel", add_channel_start)],
            states={
                WAIT_CHANNEL: [
                    MessageHandler(filters.ALL, receive_channel_forward),
                ]
            },
            fallbacks=[],
        ),
    ]
