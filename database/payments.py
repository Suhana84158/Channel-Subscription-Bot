from datetime import datetime, timezone
from database.mongo import get_database

COLLECTION = "payments"


def payments_collection():
    return get_database()[COLLECTION]


async def create_payment(
    user_id: int,
    plan: str,
    amount: float,
    screenshot_file_id: str = None,
    utr: str = None,
):
    payment = {
        "user_id": user_id,
        "plan": plan,
        "amount": amount,
        "screenshot_file_id": screenshot_file_id,
        "utr": utr,
        "status": "pending",
        "admin_id": None,
        "remarks": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    result = await payments_collection().insert_one(payment)

    payment["_id"] = result.inserted_id

    return payment


async def get_payment(payment_id):
    return await payments_collection().find_one(
        {"_id": payment_id}
    )


async def get_pending_payments():
    return await payments_collection().find(
        {"status": "pending"}
    ).to_list(length=None)


async def approve_payment(payment_id, admin_id: int):
    await payments_collection().update_one(
        {"_id": payment_id},
        {
            "$set": {
                "status": "approved",
                "admin_id": admin_id,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )


async def reject_payment(
    payment_id,
    admin_id: int,
    remarks: str = "",
):
    await payments_collection().update_one(
        {"_id": payment_id},
        {
            "$set": {
                "status": "rejected",
                "admin_id": admin_id,
                "remarks": remarks,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )


async def total_revenue():
    pipeline = [
        {"$match": {"status": "approved"}},
        {
            "$group": {
                "_id": None,
                "total": {"$sum": "$amount"},
            }
        },
    ]

    result = await payments_collection().aggregate(
        pipeline
    ).to_list(length=1)

    if result:
        return result[0]["total"]

    return 0
