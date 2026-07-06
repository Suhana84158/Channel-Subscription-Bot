import asyncio
import logging

from telegram.ext import (
    Application,
)

from config import BOT_TOKEN
from logging_config import setup_logging
from keep_alive import keep_alive
from scheduler import start_scheduler

logger = logging.getLogger(__name__)

from database.mongo import connect_database
from database.admins import initialize_admins

from handlers.plans import plans_handler
from handlers.profile import profile_callback
from handlers.payment import payment_handler
from handlers.subscription import subscription_callback
from handlers.referral import referral_callback
from handlers.broadcast import broadcast_handler
from handlers.statistics import statistics_handler
from handlers.admin import admin_handlers

async def post_init(application: Application):
    """
    Runs after bot startup.
    """

    logger.info("Connecting to MongoDB...")

    await connect_database()

    await initialize_admins()

    start_scheduler()

    logger.info("Bot started successfully.")


def build_application():

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    return application
from telegram import Update
from telegram.ext import ContextTypes

# Handler imports
from handlers.start import start_command
from handlers.errors import error_handler


async def register_handlers(application: Application):

    application.add_handler(start_command())
    application.add_handler(plans_handler())
    application.add_handler(profile_callback())
    application.add_handler(payment_handler())
    application.add_handler(subscription_callback())
    application.add_handler(referral_callback())
    application.add_handler(broadcast_handler())
    application.add_handler(statistics_handler())

    for handler in admin_handlers():
        application.add_handler(handler)

    application.add_error_handler(error_handler)

    logger.info("All handlers registered.")
    async def main():

    setup_logging()

    logger.info("Starting Telegram Subscription Bot...")

    keep_alive()

    application = build_application()

    await register_handlers(application)

    logger.info("Bot initialization completed.")

    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    await asyncio.Event().wait()
    if __name__ == "__main__":
    asyncio.run(main())
