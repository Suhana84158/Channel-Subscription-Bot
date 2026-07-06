from telegram import Update
from telegram.ext import MessageHandler, filters, ContextTypes

from database.payments import create_payment
from database.users import get_user
from database.admins import get_admins
from config import ADMIN_GROUP_ID


async def handle_payment_screenshot(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user

    if not update.message.photo:
        return

    photo = update.message.photo[-1].file_id

    user_data = await get_user(user.id)

    payment = await create_payment(
        user_id=user.id,
        username=user.username,
        screenshot=photo,
        status="pending",
    )

    text = (
        "🆕 *New Payment Request*\n\n"
        f"👤 User: {user.first_name}\n"
        f"🆔 ID: `{user.id}`\n"
        f"📌 Status: Pending\n\n"
        "Use admin panel to approve or reject."
    )

    admins = await get_admins()

    for admin in admins:
        try:
            await context.bot.send_photo(
                chat_id=admin["user_id"],
                photo=photo,
                caption=text,
            )
        except:
            pass

    await update.message.reply_text(
        "✅ Payment received! Waiting for approval."
    )


def payment_upload_handler():
    return MessageHandler(
        filters.PHOTO,
        handle_payment_screenshot,
    )
