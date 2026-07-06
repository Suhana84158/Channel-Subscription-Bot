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


async def post_init(application: Application):
    """
    Runs after bot startup.
    """

    logger.info("Bot started successfully.")

    start_scheduler()


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
    """
    Register all bot handlers.
    """

    application.add_handler(start_command())

    application.add_error_handler(error_handler)

    logger.info("Handlers registered successfully.")
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
