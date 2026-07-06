from services.subscription_service import activate_subscription
from services.channel_service import grant_channel_access
from database.payments import update_payment_status
from database.admins import is_admin


async def approve_payment(update, context):
    query = update.callback_query
    await query.answer()

    admin_id = query.from_user.id

    # ❌ security check
    if not await is_admin(admin_id):
        await query.edit_message_text("❌ Not authorized")
        return

    try:
        # callback data: approve_12345_30
        data = query.data.split("_")

        user_id = int(data[1])

        # default plan days = 30 (safe fallback)
        plan_days = int(data[2]) if len(data) > 2 else 30

        # update payment status
        await update_payment_status(user_id, "approved")

        # activate subscription
        await activate_subscription(user_id, plan_days=plan_days)

        # grant channel access
        await grant_channel_access(user_id)

        # update admin message
        await query.edit_message_text(
            f"✅ Payment Approved\n\nUser ID: {user_id}\nPlan: {plan_days} days"
        )

        # notify user
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "🎉 Payment Approved!\n\n"
                    f"Your subscription is active for {plan_days} days."
                ),
            )
        except:
            pass

    except Exception as e:
        await query.edit_message_text(f"❌ Error: {str(e)}")
