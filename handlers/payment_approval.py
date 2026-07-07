from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from database.admins import is_admin
from database.payments import update_payment_status
from services.subscription_service import activate_subscription
from services.channel_service import grant_channel_access


async def safe_edit(query, text: str):
    try:
        await query.edit_message_caption(caption=text)
    except Exception:
        try:
            await query.edit_message_text(text)
        except Exception:
            pass


async def approve_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    admin_id = query.from_user.id

    if not await is_admin(admin_id):
        await safe_edit(query, "❌ Not authorized")
        return

    try:
        data = query.data.split("_")
        user_id = int(data[1])
        plan_days = int(data[2]) if len(data) > 2 else 30

        await update_payment_status(
            user_id=user_id,
            status="approved",
            admin_id=admin_id,
        )

        await activate_subscription(
            user_id=user_id,
            plan_days=plan_days,
        )

        await grant_channel_access(user_id)

        await safe_edit(
            query,
            f"✅ Payment Approved\n\n"
            f"User ID: {user_id}\n"
            f"Duration: {plan_days} days",
        )

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "🎉 Payment Approved!\n\n"
                f"Your subscription is active for {plan_days} days."
            ),
        )

    except Exception as e:
        await safe_edit(query, f"❌ Error:\n{e}")


async def reject_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    admin_id = query.from_user.id

    if not await is_admin(admin_id):
        await safe_edit(query, "❌ Not authorized")
        return

    try:
        data = query.data.split("_")
        user_id = int(data[1])

        await update_payment_status(
            user_id=user_id,
            status="rejected",
            admin_id=admin_id,
        )

        await safe_edit(
            query,
            f"❌ Payment Rejected\nUser ID: {user_id}",
        )

        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Your payment was rejected. Please try again.",
        )

    except Exception as e:
        await safe_edit(query, f"❌ Error:\n{e}")


def payment_approval_handlers():
    return [
        CallbackQueryHandler(approve_payment, pattern=r"^approve_"),
        CallbackQueryHandler(reject_payment, pattern=r"^reject_"),
    ]
