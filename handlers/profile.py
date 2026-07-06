from telegram import (
    Update,
)
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
)

from database.users import get_user
from database.subscriptions import get_subscription


async def profile_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    await query.answer()

    user = await get_user(query.from_user.id)

    subscription = await get_subscription(
        query.from_user.id
    )

    if subscription:
        plan = subscription.get("plan", "N/A")
        expiry = subscription.get("expiry_date", "N/A")
        status = "✅ Active" if subscription.get("active") else "❌ Expired"
    else:
        plan = "No Plan"
        expiry = "-"
        status = "Inactive"

    text = (
        "👤 *My Profile*\n\n"
        f"🆔 ID: `{user['user_id']}`\n"
        f"👤 Name: {user['first_name']}\n"
        f"📛 Username: @{user['username'] if user['username'] else 'None'}\n\n"
        f"💎 Plan: {plan}\n"
        f"📅 Expiry: {expiry}\n"
        f"📌 Status: {status}"
    )

    await query.edit_message_text(
        text=text,
        parse_mode="Markdown",
    )


def profile_callback():
    return CallbackQueryHandler(
        profile_handler,
        pattern="^profile$",
    )
