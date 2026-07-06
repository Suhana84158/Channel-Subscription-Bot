from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes

from database.payments import update_payment_status
from database.subscriptions import activate_subscription
from database.admins import is_admin


# -----------------------------
# APPROVE PAYMENT
# -----------------------------
async def approve_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    admin_id = query.from_user.id

    if not await is_admin(admin_id):
        await query.edit_message_text("❌ Not authorized")
        return

    data = query.data.split("_")  # approve_userid
    user_id = int(data[1])

    await update_payment_status(user_id, "approved")
    await activate_subscription(user_id)

    await query.edit_message_text(
        f"✅ Payment Approved\nUser ID: {user_id}"
    )

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text="🎉 Payment Approved!\nYour subscription is now active.",
        )
    except:
        pass


# -----------------------------
# REJECT PAYMENT
# -----------------------------
async def reject_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    admin_id = query.from_user.id

    if not await is_admin(admin_id):
        await query.edit_message_text("❌ Not authorized")
        return

    data = query.data.split("_")  # reject_userid
    user_id = int(data[1])

    await update_payment_status(user_id, "rejected")

    await query.edit_message_text(
        f"❌ Payment Rejected\nUser ID: {user_id}"
    )

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Payment rejected. Please try again.",
        )
    except:
        pass


# -----------------------------
# HANDLER REGISTRATION
# -----------------------------
def payment_approval_handlers():
    return [
        CallbackQueryHandler(approve_payment, pattern="^approve_"),
        CallbackQueryHandler(reject_payment, pattern="^reject_"),
    ]
