from datetime import datetime, timezone

from database.mongo import get_database

COLLECTION = "seller_bots"


def seller_bots_collection():
    return get_database()[COLLECTION]


async def get_bot(owner_id: int):
    return await seller_bots_collection().find_one(
        {"owner_id": owner_id}
    )


async def save_bot(
    owner_id: int,
    bot_id: int,
    bot_name: str,
    bot_username: str,
    bot_token: str,
):
    now = datetime.now(timezone.utc)

    await seller_bots_collection().update_one(
        {"owner_id": owner_id},
        {
            "$set": {
                "bot_id": bot_id,
                "bot_name": bot_name,
                "bot_username": bot_username,
                "bot_token": bot_token,
                "active": True,
                "updated_at": now,
            },
            "$setOnInsert": {
                "created_at": now,
            },
        },
        upsert=True,
    )


async def delete_bot(owner_id: int):
    await seller_bots_collection().delete_one(
        {"owner_id": owner_id}
    )


async def bot_exists(owner_id: int):
    return await seller_bots_collection().count_documents(
        {"owner_id": owner_id}
    ) > 0


async def total_bots():
    return await seller_bots_collection().count_documents({})
