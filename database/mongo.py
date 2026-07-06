from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure

from config import MONGO_URI, DATABASE_NAME
from logging_config import get_logger

logger = get_logger(__name__)

client = None
db = None


async def connect_database():
    global client, db

    try:
        client = AsyncIOMotorClient(MONGO_URI)

        await client.admin.command("ping")

        db = client[DATABASE_NAME]

        logger.info("MongoDB connected successfully.")

    except ConnectionFailure as e:
        logger.exception("MongoDB connection failed.")
        raise e


def get_database():
    if db is None:
        raise RuntimeError(
            "Database is not initialized."
        )

    return db


async def close_database():
    global client

    if client:
        client.close()
        logger.info("MongoDB connection closed.")
