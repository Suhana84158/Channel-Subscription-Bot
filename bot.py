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
