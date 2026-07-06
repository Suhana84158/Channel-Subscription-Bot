from datetime import datetime, timezone

from database.mongo import get_database

COLLECTION = "channels"


def channels_collection():
    return get_database()[COLLECTION]


async def add_channel(chat_id: int, title: str):
    await channels_collection().update_one(
        {"chat_id": chat_id},
        {
            "$set": {
                "title": title,
                "active": True,
                "updated_at": datetime.now(timezone.utc),
            },
            "$setOnInsert": {
                "created_at": datetime.now(timezone.utc),
            },
        },
        upsert=True,
    )


async def remove_channel(chat_id: int):
    await channels_collection().update_one(
        {"chat_id": chat_id},
        {
            "$set": {
                "active": False,
                "updated_at": datetime.now(timezone.utc),
            }
        }
    )


async def get_channel(chat_id: int):
    return await channels_collection().find_one(
        {"chat_id": chat_id}
    )


async def get_active_channels():
    return await channels_collection().find(
        {"active": True}
    ).to_list(length=None)


async def total_channels():
    return await channels_collection().count_documents(
        {"active": True}
    )
