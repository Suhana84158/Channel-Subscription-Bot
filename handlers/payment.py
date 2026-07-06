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


async def buy_subscription(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    await query.answer()

    text = (
        "💳 *Subscription Payment*\n\n"
        f"👤 UPI Name: {UPI_NAME}\n"
        f"🏦 UPI ID: `{UPI_ID}`\n\n"
        "✅ Scan the QR Code or pay using the UPI ID.\n\n"
        "📷 After payment, send:\n"
        "• Payment Screenshot\n"
        "• UTR / Transaction ID"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "📤 Upload Screenshot",
                callback_data="upload_payment",
            )
        ]
    ]

    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


def payment_handler():
    return CallbackQueryHandler(
        buy_subscription,
        pattern="^buy$",
    )
