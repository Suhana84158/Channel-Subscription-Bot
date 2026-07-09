from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
)

from config import UPI_ID, UPI_NAME
from handlers.plans import get_plan


async def buy_subscription(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    plan_key = query.data.replace("buy_", "")

    plan = get_plan(plan_key)

    if not plan:
        await query.answer(
            "Invalid plan selected.",
            show_alert=True,
        )
        return

    context.user_data["selected_plan"] = plan

    text = (
        "💳 *Subscription Payment*\n\n"
        f"📦 Plan: *{plan['name']}*\n"
        f"💰 Amount: ₹{plan['price']}\n"
        f"⏳ Duration: *{plan['duration_text']}*\n\n"
        f"👤 UPI Name: {UPI_NAME}\n"
        f"🏦 UPI ID: `{UPI_ID}`\n\n"
        "After payment upload your payment screenshot."
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "📤 Upload Screenshot",
                callback_data="upload_payment",
            )
        ],
        [
            InlineKeyboardButton(
                "⬅ Back",
                callback_data="plans",
            )
        ],
    ]

    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


def payment_handler():
    return CallbackQueryHandler(
        buy_subscription,
        pattern=r"^buy_",
    )
