from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
)

PLANS = [
    {
        "name": "Basic",
        "days": 30,
        "price": 99,
    },
    {
        "name": "Premium",
        "days": 90,
        "price": 249,
    },
    {
        "name": "Ultimate",
        "days": 365,
        "price": 799,
    },
]


async def show_plans(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    await query.answer()

    text = "📋 *Available Subscription Plans*\n\n"

    keyboard = []

    for plan in PLANS:
        text += (
            f"• *{plan['name']}*\n"
            f"💰 ₹{plan['price']}\n"
            f"📅 {plan['days']} Days\n\n"
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"Buy {plan['name']}",
                    callback_data=f"buy_{plan['name']}",
                )
            ]
        )

    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


def plans_handler():
    return CallbackQueryHandler(
        show_plans,
        pattern="^plans$",
    )
