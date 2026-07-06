from database.mongo import get_database

COLLECTION = "channels"


def channels_collection():
    return get_database()[COLLECTION]


async def add_channel(chat_id: int, title: str):
    await channels_collection().update_one(
        {"chat_id": chat_id},
        {
            "$set": {
                "chat_id": chat_id,
                "title": title,
            }
        },
        upsert=True,
    )


async def remove_channel(chat_id: int):
    await channels_collection().delete_one(
        {"chat_id": chat_id}
    )


async def get_all_channels():
    return await channels_collection().find({}).to_list(length=None)


# ✅ ADD THIS (REQUIRED FOR STATISTICS)
async def total_channels():
    return await channels_collection().count_documents({})
