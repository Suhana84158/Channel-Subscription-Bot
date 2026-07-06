from datetime import datetime, timezone

from database.mongo import get_database


COLLECTION = "users"


def users_collection():
    return get_database()[COLLECTION]


async def get_user(user_id: int):
    return await users_collection().find_one(
        {"user_id": user_id}
    )


async def create_user(user):
    document = {
        "user_id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "is_bot": user.is_bot,
        "language_code": user.language_code,
        "joined_at": datetime.now(timezone.utc),
        "subscription": {
            "active": False,
            "plan": None,
            "expiry": None,
        },
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    await users_collection().insert_one(document)

    return document


async def get_or_create_user(user):
    existing = await get_user(user.id)

    if existing:
        return existing

    return await create_user(user)


async def update_user(user_id: int, data: dict):
    data["updated_at"] = datetime.now(timezone.utc)

    await users_collection().update_one(
        {"user_id": user_id},
        {
            "$set": data
        }
    )


async def total_users():
    return await users_collection().count_documents({})
