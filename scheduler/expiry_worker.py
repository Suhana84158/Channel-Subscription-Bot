from datetime import datetime, timezone

from database.subscriptions import (
    get_all_subscriptions,
    expire_subscription,
)
from services.channel_service import revoke_channel_access

from logging_config import get_logger

logger = get_logger(__name__)


async def check_expired_users():
    """
    Auto remove expired subscriptions
    """

    now = datetime.now(timezone.utc)

    subscriptions = await get_all_subscriptions()

    for sub in subscriptions:
        try:
            user_id = sub["user_id"]
            expiry_date = sub.get("expiry_date")

            if not expiry_date:
                continue

            # Convert naive datetime to UTC aware datetime
            if expiry_date.tzinfo is None:
                expiry_date = expiry_date.replace(tzinfo=timezone.utc)

            if expiry_date <= now:
                await revoke_channel_access(user_id)
                await expire_subscription(user_id)

                logger.info(
                    f"Expired user removed: {user_id}"
                )

        except Exception as e:
            logger.exception(e)
