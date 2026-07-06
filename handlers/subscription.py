from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
)

from database.subscriptions import get_subscription


async def subscription_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    await query.answer()

    subscription = await get_subscription(
        query.from_user.id
    )

    if not subscription:
        await query.edit_message_text(
            "❌ You don't have any active subscription."
        )
        return

    status = (
        "✅ Active"
        if subscription.get("active")
        else "❌ Expired"
    )

    text = (
        "💎 *My Subscription*\n\n"
        f"📦 Plan: {subscription.get('plan')}\n"
        f"📅 Expiry: {subscription.get('expiry_date')}\n"
        f"📌 Status: {status}"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "🔄 Renew Subscription",
                callback_data="renew",
            )
        ]
    ]

    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


def subscription_callback():
    return CallbackQueryHandler(
        subscription_handler,
        pattern="^subscription$",
    )
