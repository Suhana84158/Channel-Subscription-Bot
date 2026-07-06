from datetime import datetime, timedelta, timezone

from database.mongo import get_database

COLLECTION = "subscriptions"


def subscriptions_collection():
    return get_database()[COLLECTION]


async def activate_subscription(
    user_id: int,
    plan_name: str,
    duration_days: int,
):
    now = datetime.now(timezone.utc)
    expiry = now + timedelta(days=duration_days)

    await subscriptions_collection().update_one(
        {"user_id": user_id},
        {
            "$set": {
                "user_id": user_id,
                "plan": plan_name,
                "active": True,
                "start_date": now,
                "expiry_date": expiry,
                "updated_at": now,
            },
            "$setOnInsert": {
                "created_at": now,
            },
        },
        upsert=True,
    )

    return expiry


async def get_subscription(user_id: int):
    return await subscriptions_collection().find_one(
        {"user_id": user_id}
    )


async def renew_subscription(
    user_id: int,
    duration_days: int,
):
    subscription = await get_subscription(user_id)

    now = datetime.now(timezone.utc)

    if (
        subscription
        and subscription.get("expiry_date")
        and subscription["expiry_date"] > now
    ):
        expiry = subscription["expiry_date"] + timedelta(days=duration_days)
    else:
        expiry = now + timedelta(days=duration_days)

    await subscriptions_collection().update_one(
        {"user_id": user_id},
        {
            "$set": {
                "active": True,
                "expiry_date": expiry,
                "updated_at": now,
            }
        },
        upsert=True,
    )

    return expiry


async def expire_subscription(user_id: int):
    await subscriptions_collection().update_one(
        {"user_id": user_id},
        {
            "$set": {
                "active": False,
                "updated_at": datetime.now(timezone.utc),
            }
        }
    )


async def get_expired_subscriptions():
    now = datetime.now(timezone.utc)

    return await subscriptions_collection().find(
        {
            "active": True,
            "expiry_date": {"$lte": now},
        }
    ).to_list(length=None)
