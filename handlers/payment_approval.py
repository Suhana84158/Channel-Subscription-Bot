from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from services.subscription_service import activate_subscription
from services.channel_service import grant_channel_access
from database.payments import update_payment_status
from database.admins import is_admin


async def approve_payment(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    admin_id = query.from_user.id

    if not await is_admin(admin_id):
        await query.edit_message_text(
            "❌ Not authorized."
        )
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

        await query.edit_message_text(
            f"✅ Payment Approved\n\n"
            f"User ID: {user_id}\n"
            f"Duration: {plan_days} days"
        )

        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "🎉 Payment Approved!\n\n"
                    f"Subscription activated for {plan_days} days."
                ),
            )
        except Exception:
            pass

    except Exception as e:
        await query.edit_message_text(
            f"❌ Error:\n{e}"
        )


def payment_approval_handlers():
    return [
        CallbackQueryHandler(
            approve_payment,
            pattern=r"^approve_",
        )
    ]
