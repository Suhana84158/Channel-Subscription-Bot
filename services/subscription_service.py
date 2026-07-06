from datetime import datetime, timedelta, timezone

from database.subscriptions import (
    create_subscription,
    update_subscription,
)

from database.channels import get_all_channels

from logging_config import get_logger

logger = get_logger(__name__)


# -------------------------
# ACTIVATE SUBSCRIPTION
# -------------------------
async def activate_subscription(user_id: int, plan_days: int):
    """
    Activate user subscription after payment approval
    """

    expiry_date = datetime.now(timezone.utc) + timedelta(days=plan_days)

    await create_subscription(
        user_id=user_id,
        expiry_date=expiry_date,
        active=True,
    )

    logger.info(
        f"Subscription activated for user {user_id} until {expiry_date}"
    )

    return expiry_date


# -------------------------
# EXTEND SUBSCRIPTION
# -------------------------
async def extend_subscription(user_id: int, plan_days: int):

    expiry_date = datetime.now(timezone.utc) + timedelta(days=plan_days)

    await update_subscription(
        user_id=user_id,
        expiry_date=expiry_date,
        active=True,
    )

    return expiry_date
