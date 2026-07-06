from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
)

PLANS = {
    "Basic": {
        "name": "Basic",
        "days": 30,
        "price": 99,
    },
    "Premium": {
        "name": "Premium",
        "days": 90,
        "price": 249,
    },
    "Ultimate": {
        "name": "Ultimate",
        "days": 365,
        "price": 799,
    },
}


async def show_plans(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    text = (
        "📋 *Available Subscription Plans*\n\n"
    )

    keyboard = []

    for key, plan in PLANS.items():

        text += (
            f"⭐ *{plan['name']}*\n"
            f"💰 ₹{plan['price']}\n"
            f"📅 {plan['days']} Days\n\n"
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"Buy ₹{plan['price']}",
                    callback_data=f"buy_{key}",
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅ Back",
                callback_data="start",
            )
        ]
    )

    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


def get_plan(plan_name: str):
    return PLANS.get(plan_name)


def plans_handler():
    return CallbackQueryHandler(
        show_plans,
        pattern="^plans$",
    )
