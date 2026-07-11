from datetime import timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from database.admins import is_admin, add_admin, remove_admin
from database.channels import add_channel, remove_channel, get_all_channels, total_channels
from database.users import total_users, get_user, get_user_by_username, ban_user, unban_user
from database.payments import total_revenue
from database.settings import get_setting, get_setting_value, set_setting
from database.subscriptions import (
    get_subscription,
    expire_subscription,
    activate_subscription,
    renew_subscription,
)
from services.channel_service import revoke_channel_access, grant_channel_access

IST = ZoneInfo("Asia/Kolkata")


def format_time(dt):
    if not dt:
        return "-"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(IST).strftime("%d-%m-%Y %I:%M:%S %p IST")


def admin_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 User Management", callback_data="admin_users")],
        [InlineKeyboardButton("➕ Add Channel/Group", callback_data="admin_add_channel")],
        [InlineKeyboardButton("📋 Channel List", callback_data="admin_channels")],
        [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")],
        [InlineKeyboardButton("💳 Payment Settings", callback_data="admin_payment_settings")],
        [InlineKeyboardButton("⚙️ Bot Settings", callback_data="admin_bot_settings")],
        [InlineKeyboardButton("📨 Pending Payments", callback_data="admin_pending_payments")],
        [InlineKeyboardButton("📜 Payment History", callback_data="admin_payment_history")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("👮 Admin Commands", callback_data="admin_commands")],
    ])


def back_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅ Back", callback_data="admin_home")]])


def user_action_keyboard(user_id: int, banned: bool):
    keyboard = [
        [InlineKeyboardButton("🎁 Give Subscription", callback_data=f"user_give_sub_{user_id}")],
        [InlineKeyboardButton("⏳ Extend Subscription", callback_data=f"user_extend_sub_{user_id}")],
        [InlineKeyboardButton("❌ Remove Subscription", callback_data=f"user_remove_sub_{user_id}")],
    ]
    if banned:
        keyboard.append([InlineKeyboardButton("✅ Unban User", callback_data=f"user_unban_{user_id}")])
    else:
        keyboard.append([InlineKeyboardButton("🚫 Ban User", callback_data=f"user_ban_{user_id}")])
    keyboard.append([InlineKeyboardButton("⬅ Back", callback_data="admin_users")])
    return InlineKeyboardMarkup(keyboard)


def parse_plan_time(time_text: str):
    value = time_text.strip().lower()
    if value.endswith("m"):
        return int(value[:-1]), "minutes"
    if value.endswith("h"):
        return int(value[:-1]) * 60, "hours"
    if value.endswith("d"):
        return int(value[:-1]) * 1440, "days"
    raise ValueError("Use m, h, or d. Example: 30m, 1h, 30d")


def parse_plans(text: str):
    plans = []
    for part in text.split(","):
        duration_text, price_text = part.strip().split(":", 1)
        duration_minutes, unit = parse_plan_time(duration_text)
        price = int(price_text.strip())
        if price < 0:
            raise ValueError("Price cannot be negative")
        plans.append({
            "duration_text": duration_text.strip().lower(),
            "duration_minutes": duration_minutes,
            "duration_days": duration_minutes // 1440 if duration_minutes % 1440 == 0 else 0,
            "price": price,
            "unit": unit,
        })
    if not plans:
        raise ValueError("At least one plan is required")
    return plans


async def build_user_details_text(user):
    subscription = await get_subscription(user["user_id"])
    if subscription:
        plan = subscription.get("plan", "No Plan")
        expiry = format_time(subscription.get("expiry_date"))
        status = "✅ Active" if subscription.get("active") else "❌ Expired"
    else:
        plan, expiry, status = "No Plan", "-", "No subscription"
    return (
        "👤 User Details\n\n"
        f"🆔 ID: {user.get('user_id')}\n"
        f"👤 Name: {user.get('first_name') or '-'}\n"
        f"📛 Username: @{user.get('username') if user.get('username') else 'None'}\n"
        f"🚫 Banned: {'Yes' if user.get('banned') else 'No'}\n"
        f"📝 Reason: {user.get('ban_reason') or '-'}\n"
        f"📅 Joined: {format_time(user.get('joined_at'))}\n\n"
        f"💎 Plan: {plan}\n📅 Expiry: {expiry}\n📌 Status: {status}"
    )


async def show_user_details(query, user):
    await query.edit_message_text(
        await build_user_details_text(user),
        reply_markup=user_action_keyboard(user["user_id"], bool(user.get("banned"))),
    )


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized.")
        return
    await update.message.reply_text("🛠 Admin Panel\n\nChoose an option:", reply_markup=admin_keyboard())


async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not await is_admin(query.from_user.id):
        await query.edit_message_text("❌ You are not authorized.")
        return

    data = query.data

    if data == "admin_users":
        context.user_data.clear()
        context.user_data["waiting_user_search"] = True
        await query.edit_message_text("👥 User Management\n\nSend User ID or @username to search.", reply_markup=back_keyboard())

    elif data.startswith("user_ban_"):
        user_id = int(data.replace("user_ban_", ""))
        await ban_user(user_id, "Banned by admin")
        await revoke_channel_access(user_id)
        user = await get_user(user_id)
        await show_user_details(query, user)

    elif data.startswith("user_unban_"):
        user_id = int(data.replace("user_unban_", ""))
        await unban_user(user_id)
        user = await get_user(user_id)
        await show_user_details(query, user)

    elif data.startswith("user_give_sub_"):
        user_id = int(data.replace("user_give_sub_", ""))
        context.user_data.clear()
        context.user_data["give_sub_user"] = user_id
        await query.edit_message_text("🎁 Give Subscription\n\nSend duration: 30m, 1h, 1d, 30d", reply_markup=back_keyboard())

    elif data.startswith("user_extend_sub_"):
        user_id = int(data.replace("user_extend_sub_", ""))
        context.user_data.clear()
        context.user_data["extend_sub_user"] = user_id
        await query.edit_message_text("⏳ Extend Subscription\n\nSend duration: 30m, 1h, 1d, 30d", reply_markup=back_keyboard())

    elif data.startswith("user_remove_sub_"):
        user_id = int(data.replace("user_remove_sub_", ""))
        await expire_subscription(user_id)
        await revoke_channel_access(user_id)
        user = await get_user(user_id)
        await show_user_details(query, user)

    elif data == "admin_add_channel":
        context.user_data.clear()
        context.user_data["waiting_channel"] = True
        await query.edit_message_text("📢 Forward any message from your channel/group.\n\n⚠ Bot must be admin there.", reply_markup=back_keyboard())

    elif data == "admin_channels":
        channels = await get_all_channels()
        if not channels:
            await query.edit_message_text("📋 No channel/group added yet.", reply_markup=back_keyboard())
            return
        text, keyboard = "📋 Added Channels/Groups:\n\n", []
        for channel in channels:
            chat_id = channel.get("chat_id")
            title = channel.get("title", "Unknown")
            text += f"• {title}\nID: {chat_id}\n"
            plans = channel.get("plans", [])
            if plans:
                for plan in plans:
                    text += f"  - {plan.get('duration_text')} = ₹{plan.get('price')}\n"
            else:
                text += "  - No plans set\n"
            text += "\n"
            keyboard.append([InlineKeyboardButton(f"❌ Remove {title}", callback_data=f"admin_remove_{chat_id}")])
        keyboard.append([InlineKeyboardButton("⬅ Back", callback_data="admin_home")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("admin_remove_"):
        chat_id = int(data.replace("admin_remove_", ""))
        await remove_channel(chat_id)
        await query.edit_message_text("✅ Channel/Group removed successfully.", reply_markup=back_keyboard())

    elif data == "admin_payment_settings":
        upi = await get_setting_value("upi_id", "")
        name = await get_setting_value("upi_name", "")
        qr = await get_setting_value("upi_qr_file_id", None)
        text = (
            "💳 Payment Settings\n\n"
            f"👤 UPI Name: {name or 'Not Set'}\n"
            f"🏦 UPI ID: {upi or 'Not Set'}\n"
            f"🖼 QR Code: {'✅ Added' if qr else '❌ Not Added'}"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✏ Set UPI ID", callback_data="set_upi_id")],
            [InlineKeyboardButton("👤 Set UPI Name", callback_data="set_upi_name")],
            [InlineKeyboardButton("🖼 Upload QR", callback_data="set_upi_qr")],
            [InlineKeyboardButton("⬅ Back", callback_data="admin_home")],
        ])
        await query.edit_message_text(text, reply_markup=keyboard)

    elif data in {"set_upi_id", "set_upi_name", "set_upi_qr"}:
        context.user_data.clear()
        key_map = {
            "set_upi_id": ("waiting_upi_id", "🏦 Send the new UPI ID."),
            "set_upi_name": ("waiting_upi_name", "👤 Send the new UPI Name."),
            "set_upi_qr": ("waiting_upi_qr", "🖼 Send the QR Code image."),
        }
        state_key, prompt = key_map[data]
        context.user_data[state_key] = True
        await query.edit_message_text(prompt, reply_markup=back_keyboard())

    elif data == "admin_bot_settings":
        bot_name = await get_setting_value("bot_name", "Subscription Bot")
        support = await get_setting_value("support_username", "")
        currency = await get_setting_value("currency", "INR")
        timezone_name = await get_setting_value("timezone", "Asia/Kolkata")
        reminder_days = await get_setting_value("reminder_days", 1)
        text = (
            "⚙️ Bot Settings\n\n"
            f"🤖 Bot Name: {bot_name}\n"
            f"📞 Support: {support or 'Not Set'}\n"
            f"💵 Currency: {currency}\n"
            f"🕒 Timezone: {timezone_name}\n"
            f"🔔 Reminder: {reminder_days} day(s)"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🤖 Bot Name", callback_data="set_bot_name")],
            [InlineKeyboardButton("💬 Welcome Message", callback_data="set_welcome_message")],
            [InlineKeyboardButton("📞 Support Username", callback_data="set_support_username")],
            [InlineKeyboardButton("💵 Currency", callback_data="set_currency"), InlineKeyboardButton("🕒 Timezone", callback_data="set_timezone")],
            [InlineKeyboardButton("🔔 Reminder Days", callback_data="set_reminder_days")],
            [InlineKeyboardButton("⬅ Back", callback_data="admin_home")],
        ])
        await query.edit_message_text(text, reply_markup=keyboard)

    elif data in {"set_bot_name", "set_welcome_message", "set_support_username", "set_currency", "set_timezone", "set_reminder_days"}:
        context.user_data.clear()
        prompts = {
            "set_bot_name": ("waiting_bot_name", "🤖 Send the new Bot Name."),
            "set_welcome_message": ("waiting_welcome_message", "💬 Send the new Welcome Message."),
            "set_support_username": ("waiting_support_username", "📞 Send Support Username. Example: @YourSupport"),
            "set_currency": ("waiting_currency", "💵 Send currency code. Example: INR"),
            "set_timezone": ("waiting_timezone", "🕒 Send timezone. Example: Asia/Kolkata"),
            "set_reminder_days": ("waiting_reminder_days", "🔔 Send reminder days. Example: 1"),
        }
        state_key, prompt = prompts[data]
        context.user_data[state_key] = True
        await query.edit_message_text(prompt, reply_markup=back_keyboard())

    elif data == "admin_stats":
        await query.edit_message_text(
            f"📊 Bot Statistics\n\n👤 Users: {await total_users()}\n📢 Channels: {await total_channels()}\n💰 Revenue: ₹{await total_revenue()}",
            reply_markup=back_keyboard(),
        )

    elif data == "admin_broadcast":
        await query.edit_message_text("📢 Broadcast\n\nUse /broadcast, then send content.", reply_markup=back_keyboard())

    elif data == "admin_commands":
        await query.edit_message_text(
            "👮 Admin Commands\n\n/admin\n/addadmin USER_ID\n/removeadmin USER_ID\n/addchannel\n/removechannel CHAT_ID\n/stats\n/broadcast",
            reply_markup=back_keyboard(),
        )

    elif data in {"admin_back", "admin_home", "admin_panel"}:
        context.user_data.clear()
        await query.edit_message_text("🛠 Admin Panel\n\nChoose an option:", reply_markup=admin_keyboard())


async def receive_admin_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id):
        return
    text = (update.message.text or "").strip()

    simple_settings = [
        ("waiting_bot_name", "bot_name", "✅ Bot Name updated successfully."),
        ("waiting_welcome_message", "welcome_message", "✅ Welcome Message updated successfully."),
        ("waiting_support_username", "support_username", "✅ Support Username updated successfully."),
        ("waiting_currency", "currency", "✅ Currency updated successfully."),
        ("waiting_upi_id", "upi_id", "✅ UPI ID updated successfully."),
        ("waiting_upi_name", "upi_name", "✅ UPI Name updated successfully."),
    ]
    for state_key, setting_key, success_message in simple_settings:
        if context.user_data.get(state_key):
            if not text:
                await update.message.reply_text("❌ Value cannot be empty.")
                return
            if setting_key == "support_username" and text and not text.startswith("@"):
                text = "@" + text
            await set_setting(setting_key, text)
            context.user_data.clear()
            await update.message.reply_text(success_message, reply_markup=admin_keyboard())
            return

    if context.user_data.get("waiting_timezone"):
        try:
            ZoneInfo(text)
        except ZoneInfoNotFoundError:
            await update.message.reply_text("❌ Invalid timezone. Example: Asia/Kolkata")
            return
        await set_setting("timezone", text)
        context.user_data.clear()
        await update.message.reply_text("✅ Timezone updated successfully.", reply_markup=admin_keyboard())
        return

    if context.user_data.get("waiting_reminder_days"):
        try:
            days = int(text)
            if days < 0 or days > 365:
                raise ValueError
        except ValueError:
            await update.message.reply_text("❌ Send a number from 0 to 365.")
            return
        await set_setting("reminder_days", days)
        context.user_data.clear()
        await update.message.reply_text("✅ Reminder days updated successfully.", reply_markup=admin_keyboard())
        return

    if context.user_data.get("give_sub_user") or context.user_data.get("extend_sub_user"):
        try:
            duration_minutes, _ = parse_plan_time(text)
            duration_days = duration_minutes // 1440 if duration_minutes % 1440 == 0 else 0
            if context.user_data.get("give_sub_user"):
                user_id = context.user_data["give_sub_user"]
                expiry = await activate_subscription(user_id=user_id, plan_name="Admin Gift", duration_days=duration_days, duration_minutes=duration_minutes)
                action_text = "given"
            else:
                user_id = context.user_data["extend_sub_user"]
                expiry = await renew_subscription(user_id=user_id, duration_days=duration_days, duration_minutes=duration_minutes)
                action_text = "extended"
            await grant_channel_access(user_id)
            context.user_data.clear()
            await update.message.reply_text(
                f"✅ Subscription {action_text} successfully!\n\n👤 User ID: {user_id}\n⏳ Duration: {text}\n📅 Expiry: {format_time(expiry)}"
            )
        except Exception as exc:
            await update.message.reply_text(f"❌ Invalid duration or error.\n\nUse: 1m, 30m, 1h, 1d, 30d\n\nError: {exc}")
        return

    if context.user_data.get("waiting_user_search"):
        user = await get_user_by_username(text) if text.startswith("@") else None
        if user is None:
            try:
                user = await get_user(int(text))
            except ValueError:
                user = None
        context.user_data["waiting_user_search"] = False
        if not user:
            await update.message.reply_text("❌ User not found.", reply_markup=back_keyboard())
            return
        await update.message.reply_text(
            await build_user_details_text(user),
            reply_markup=user_action_keyboard(user["user_id"], bool(user.get("banned"))),
        )
        return

    if context.user_data.get("waiting_plans"):
        pending_channel = context.user_data.get("pending_channel")
        if not pending_channel:
            context.user_data.clear()
            await update.message.reply_text("❌ Channel data missing. Please try again.")
            return
        try:
            plans = parse_plans(text)
            await add_channel(chat_id=pending_channel["chat_id"], title=pending_channel["title"], plans=plans)
            context.user_data.clear()
            details = "\n".join(f"• {p['duration_text']} = ₹{p['price']}" for p in plans)
            await update.message.reply_text(
                f"✅ Channel/Group added successfully!\n\nTitle: {pending_channel['title']}\nID: {pending_channel['chat_id']}\n\nPlans:\n{details}"
            )
        except Exception:
            await update.message.reply_text("❌ Invalid plan format.\n\nUse: 5m:10, 1h:20, 1d:99")


async def receive_upi_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id) or not context.user_data.get("waiting_upi_qr"):
        return
    if not update.message or not update.message.photo:
        await update.message.reply_text("❌ Please send a QR image.")
        return
    await set_setting("upi_qr_file_id", update.message.photo[-1].file_id)
    context.user_data.clear()
    await update.message.reply_text("✅ QR Code updated successfully.", reply_markup=admin_keyboard())


async def add_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized.")
        return
    context.user_data.clear()
    context.user_data["waiting_channel"] = True
    await update.message.reply_text("📢 Forward any message from your channel/group.\n\n⚠ Bot must be admin there.")


async def receive_channel_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update.effective_user.id) or not context.user_data.get("waiting_channel"):
        return
    message = update.message
    chat = getattr(message, "forward_from_chat", None)
    if chat is None:
        origin = getattr(message, "forward_origin", None)
        chat = getattr(origin, "chat", None)
    if chat is None:
        await message.reply_text("❌ Channel/group detect nahi hua. Please wahan se message forward karo.")
        return
    context.user_data["pending_channel"] = {"chat_id": chat.id, "title": chat.title or "Unknown"}
    context.user_data["waiting_channel"] = False
    context.user_data["waiting_plans"] = True
    await message.reply_text(
        f"✅ Channel detected!\n\nTitle: {chat.title}\nID: {chat.id}\n\nNow send plans:\n5m:10, 1h:20, 1d:99"
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
    await update.message.reply_text(
        f"📊 Bot Statistics\n\n👤 Users: {await total_users()}\n📢 Channels: {await total_channels()}\n💰 Revenue: ₹{await total_revenue()}"
    )


def admin_handlers():
    return [
        CommandHandler("admin", admin_panel),
        CommandHandler("stats", stats_command),
        CommandHandler("addadmin", add_admin_command),
        CommandHandler("removeadmin", remove_admin_command),
        CommandHandler("addchannel", add_channel_start),
        CommandHandler("removechannel", remove_channel_command),
        CallbackQueryHandler(admin_buttons, pattern=r"^(admin_|user_|set_)") ,
        MessageHandler(filters.FORWARDED, receive_channel_forward),
        MessageHandler(filters.TEXT & ~filters.COMMAND, receive_admin_text),
    ]
