python-telegram-bot[job-queue]==22.2
pymongo==4.8.0
motor==3.5.1
python-dotenv==1.0.1
Flask==3.0.3
gunicorn==23.0.0
APScheduler==3.10.4
qrcode==7.4.2
Pillow==10.4.0
pytz==2024.1
dnspython==2.6.1
httpx==0.28.1
aiofiles==24.1.0
cachetools==5.5.0
# Telegram Bot
BOT_TOKEN=YOUR_BOT_TOKEN

# MongoDB
MONGO_URI=mongodb+srv://USERNAME:PASSWORD@cluster.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=telegram_subscription_bot

# Bot
BOT_USERNAME=YourBotUsername

# Admin IDs (comma separated)
ADMIN_IDS=123456789,987654321

# Payment
UPI_ID=yourupi@upi
UPI_NAME=Your Name
QR_IMAGE=assets/upi_qr.png

# Subscription
DEFAULT_PLAN_DAYS=30

# Flask
PORT=10000

# Timezone
TIMEZONE=Asia/Kolkata
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")

BOT_USERNAME = os.getenv("BOT_USERNAME")

ADMIN_IDS = [
    int(x)
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip()
]

UPI_ID = os.getenv("UPI_ID")
UPI_NAME = os.getenv("UPI_NAME")
QR_IMAGE = os.getenv("QR_IMAGE")

DEFAULT_PLAN_DAYS = int(
    os.getenv("DEFAULT_PLAN_DAYS", "30")
)

PORT = int(os.getenv("PORT", "10000"))

TIMEZONE = os.getenv(
    "TIMEZONE",
    "Asia/Kolkata"
)
from flask import Flask
from threading import Thread
import os

app = Flask(__name__)


@app.route("/")
def home():
    return {
        "status": "online",
        "service": "Telegram Subscription Bot"
    }


@app.route("/health")
def health():
    return {
        "status": "healthy"
    }


def run():
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )


def keep_alive():
    Thread(target=run, daemon=True).start()
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone
from config import TIMEZONE

scheduler = AsyncIOScheduler(
    timezone=timezone(TIMEZONE)
)


def start_scheduler():
    if not scheduler.running:
        scheduler.start()


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)


def add_job(
    func,
    trigger,
    job_id,
    replace_existing=True,
    **kwargs
):
    scheduler.add_job(
        func=func,
        trigger=trigger,
        id=job_id,
        replace_existing=replace_existing,
        **kwargs
    )


def remove_job(job_id):
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass


def get_job(job_id):
    return scheduler.get_job(job_id)


def get_jobs():
    return scheduler.get_jobs()
import asyncio
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import BOT_TOKEN
from keep_alive import keep_alive
from scheduler import start_scheduler

# ========= Handlers =========
from handlers.start import start
from handlers.admin import (
    admin_panel,
    admin_callback,
)

from handlers.payment import (
    payment_menu,
    payment_screenshot,
)

from handlers.subscription import (
    my_subscription,
)

from handlers.broadcast import (
    broadcast_start,
    broadcast_message,
)

from handlers.stats import (
    user_stats,
    revenue_stats,
)

# ============================

logging.basicConfig(
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):
    logger.exception(
        "Unhandled exception:",
        exc_info=context.error,
    )


def register_handlers(application: Application):

    # User Commands
    application.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    application.add_handler(
        CommandHandler(
            "subscription",
            my_subscription,
        )
    )

    application.add_handler(
        CommandHandler(
            "pay",
            payment_menu,
        )
    )

    # Admin Commands
    application.add_handler(
        CommandHandler(
            "admin",
            admin_panel,
        )
    )

    application.add_handler(
        CommandHandler(
            "broadcast",
            broadcast_start,
        )
    )

    application.add_handler(
        CommandHandler(
            "users",
            user_stats,
        )
    )

    application.add_handler(
        CommandHandler(
            "revenue",
            revenue_stats,
        )
    )

    # Callback Buttons
    application.add_handler(
        CallbackQueryHandler(
            admin_callback,
            pattern="^admin_",
        )
    )

    # Payment Screenshot
    application.add_handler(
        MessageHandler(
            filters.PHOTO,
            payment_screenshot,
        )
    )

    # Broadcast Text
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            broadcast_message,
        )
    )

    application.add_error_handler(
        error_handler
    )


def create_application():

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    register_handlers(app)

    return app
# ============================
# bot.py (Part 2/2)
# ============================

async def post_init(application: Application):
    logger.info("Starting scheduler...")
    start_scheduler()
    logger.info("Scheduler started.")

    logger.info("Bot is ready.")


async def post_shutdown(application: Application):
    logger.info("Stopping bot...")
    logger.info("Bot stopped.")


def main():
    logger.info("Starting Flask keep_alive...")
    keep_alive()

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    register_handlers(application)

    logger.info("Starting Telegram polling...")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
        close_loop=False,
    )


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.exception("Fatal error: %s", e)
web: python bot.py
services:
  - type: web
    name: telegram-subscription-bot
    runtime: python
    plan: free

    buildCommand: |
      pip install -r requirements.txt

    startCommand: |
      python bot.py

    envVars:
      - key: BOT_TOKEN
        sync: false

      - key: MONGO_URI
        sync: false

      - key: DATABASE_NAME
        value: telegram_subscription_bot

      - key: BOT_USERNAME
        sync: false

      - key: ADMIN_IDS
        sync: false

      - key: UPI_ID
        sync: false

      - key: UPI_NAME
        sync: false

      - key: QR_IMAGE
        value: assets/upi_qr.png

      - key: DEFAULT_PLAN_DAYS
        value: "30"

      - key: TIMEZONE
        value: Asia/Kolkata

      - key: PORT
        value: "10000"

    autoDeploy: true
# Telegram Subscription Bot

A production-ready Telegram Subscription Bot built with **Python**, **python-telegram-bot v22**, **MongoDB**, **APScheduler**, and **Flask**.

---

## Features

- Multi-channel support
- Multi-admin support
- MongoDB
- UPI QR payment
- Payment screenshot verification
- Admin approve/reject
- Auto invite links
- Auto remove after subscription expiry
- Renew subscription
- Broadcast
- User statistics
- Revenue statistics
- APScheduler
- Flask keep_alive
- Render deployment ready

---

## Project Structure

```
telegram-subscription-bot/
│
├── bot.py
├── config.py
├── keep_alive.py
├── scheduler.py
├── requirements.txt
├── Procfile
├── render.yaml
├── README.md
├── .env.example
│
├── database/
├── handlers/
├── keyboards/
├── utils/
└── assets/
```

---

## Requirements

- Python 3.11+
- MongoDB Atlas
- Telegram Bot Token
- Bot must be admin in all subscription channels

---

## Installation

### Clone Repository

```bash
git clone https://github.com/yourusername/telegram-subscription-bot.git
cd telegram-subscription-bot
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment

Copy:

```
.env.example
```

to

```
.env
```

Fill all required values.

---

## Run Locally

```bash
python bot.py
```

---

## Deploy on Render

1. Push project to GitHub.
2. Create a new Render Web Service.
3. Connect your GitHub repository.
4. Render automatically detects `render.yaml`.
5. Add all Environment Variables.
6. Deploy.

---

## Environment Variables

```
BOT_TOKEN=
MONGO_URI=
DATABASE_NAME=
BOT_USERNAME=
ADMIN_IDS=

UPI_ID=
UPI_NAME=
QR_IMAGE=

DEFAULT_PLAN_DAYS=30

TIMEZONE=Asia/Kolkata

PORT=10000
```

---

## Main Modules

### User

- Start
- Subscription Status
- Payment
- Renew

### Admin

- Multi Admin
- Broadcast
- Statistics
- Revenue
- Payment Verification

### Scheduler

- Auto Expiry
- Auto Remove
- Renewal Reminder

### Database

- Users
- Admins
- Channels
- Payments
- Subscriptions

---

## Technology Stack

- Python 3
- python-telegram-bot v22
- MongoDB
- APScheduler
- Flask
- Gunicorn

---

## License

MIT License
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from config import (
    MONGO_URI,
    DATABASE_NAME,
)

# ----------------------------
# Async Client
# ----------------------------

async_client = AsyncIOMotorClient(MONGO_URI)

db = async_client[DATABASE_NAME]

# ----------------------------
# Sync Client
# ----------------------------

sync_client = MongoClient(MONGO_URI)

sync_db = sync_client[DATABASE_NAME]

# ----------------------------
# Collections
# ----------------------------

users = db.users

admins = db.admins

channels = db.channels

payments = db.payments

subscriptions = db.subscriptions

settings = db.settings

logs = db.logs


# ----------------------------
# Database Helpers
# ----------------------------

async def ping_database():
    try:
        await async_client.admin.command("ping")
        return True
    except Exception:
        return False


async def close_database():
    async_client.close()
from datetime import datetime

from database.mongo import users


async def create_user(user):
    """Create user if not exists."""

    data = {
        "_id": user.id,
        "user_id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "language_code": user.language_code,
        "is_bot": user.is_bot,
        "is_active": True,
        "subscription_active": False,
        "subscription_expiry": None,
        "joined_channels": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    await users.update_one(
        {"_id": user.id},
        {
            "$setOnInsert": data,
            "$set": {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
                "updated_at": datetime.utcnow(),
            },
        },
        upsert=True,
    )


async def get_user(user_id: int):
    return await users.find_one({"_id": user_id})


async def user_exists(user_id: int):
    return await users.find_one({"_id": user_id}) is not None


async def update_user(user_id: int, data: dict):
    data["updated_at"] = datetime.utcnow()

    await users.update_one(
        {"_id": user_id},
        {"$set": data},
    )


async def activate_subscription(user_id: int, expiry):
    await users.update_one(
        {"_id": user_id},
        {
            "$set": {
                "subscription_active": True,
                "subscription_expiry": expiry,
                "updated_at": datetime.utcnow(),
            }
        },
    )


async def deactivate_subscription(user_id: int):
    await users.update_one(
        {"_id": user_id},
        {
            "$set": {
                "subscription_active": False,
                "subscription_expiry": None,
                "updated_at": datetime.utcnow(),
            }
        },
    )


async def delete_user(user_id: int):
    await users.delete_one({"_id": user_id})


async def total_users():
    return await users.count_documents({})


async def active_users():
    return await users.count_documents(
        {
            "subscription_active": True
        }
    )


async def inactive_users():
    return await users.count_documents(
        {
            "subscription_active": False
        }
    )


async def get_all_users():
    cursor = users.find({})
    return await cursor.to_list(length=None)


async def get_expired_users():
    cursor = users.find(
        {
            "subscription_active": True,
            "subscription_expiry": {
                "$lte": datetime.utcnow()
            },
        }
    )

    return await cursor.to_list(length=None)


async def add_joined_channel(
    user_id: int,
    channel_id: int,
):
    await users.update_one(
        {"_id": user_id},
        {
            "$addToSet": {
                "joined_channels": channel_id
            }
        },
    )


async def remove_joined_channel(
    user_id: int,
    channel_id: int,
):
    await users.update_one(
        {"_id": user_id},
        {
            "$pull": {
                "joined_channels": channel_id
            }
        },
    )
from datetime import datetime

from database.mongo import admins
from config import ADMIN_IDS


async def initialize_admins():
    """
    Insert default admins from .env
    """

    for admin_id in ADMIN_IDS:

        admin = await admins.find_one(
            {
                "_id": admin_id
            }
        )

        if admin is None:

            await admins.insert_one(
                {
                    "_id": admin_id,
                    "admin_id": admin_id,
                    "role": "owner",
                    "is_active": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            )


async def is_admin(user_id: int) -> bool:
    admin = await admins.find_one(
        {
            "_id": user_id,
            "is_active": True,
        }
    )

    return admin is not None


async def get_admin(user_id: int):
    return await admins.find_one(
        {
            "_id": user_id
        }
    )


async def get_all_admins():
    cursor = admins.find(
        {
            "is_active": True
        }
    )

    return await cursor.to_list(length=None)


async def add_admin(
    user_id: int,
    role: str = "admin",
):
    await admins.update_one(
        {
            "_id": user_id
        },
        {
            "$set": {
                "admin_id": user_id,
                "role": role,
                "is_active": True,
                "updated_at": datetime.utcnow(),
            },
            "$setOnInsert": {
                "created_at": datetime.utcnow(),
            },
        },
        upsert=True,
    )


async def remove_admin(user_id: int):
    await admins.update_one(
        {
            "_id": user_id
        },
        {
            "$set": {
                "is_active": False,
                "updated_at": datetime.utcnow(),
            }
        },
    )


async def restore_admin(user_id: int):
    await admins.update_one(
        {
            "_id": user_id
        },
        {
            "$set": {
                "is_active": True,
                "updated_at": datetime.utcnow(),
            }
        },
    )


async def delete_admin(user_id: int):
    await admins.delete_one(
        {
            "_id": user_id
        }
    )


async def total_admins():
    return await admins.count_documents(
        {
            "is_active": True
        }
    )


async def get_admin_role(user_id: int):
    admin = await admins.find_one(
        {
            "_id": user_id
        }
    )

    if not admin:
        return None

    return admin.get("role", "admin")


async def change_role(
    user_id: int,
    role: str,
):
    await admins.update_one(
        {
            "_id": user_id
        },
        {
            "$set": {
                "role": role,
                "updated_at": datetime.utcnow(),
            }
        },
    )
from datetime import datetime

from database.mongo import channels


async def add_channel(
    channel_id: int,
    title: str,
    username: str = None,
):
    """
    Add or update a subscription channel.
    """

    await channels.update_one(
        {"_id": channel_id},
        {
            "$set": {
                "channel_id": channel_id,
                "title": title,
                "username": username,
                "is_active": True,
                "updated_at": datetime.utcnow(),
            },
            "$setOnInsert": {
                "created_at": datetime.utcnow(),
            },
        },
        upsert=True,
    )


async def get_channel(channel_id: int):
    return await channels.find_one(
        {
            "_id": channel_id
        }
    )


async def get_all_channels():
    cursor = channels.find(
        {
            "is_active": True
        }
    )

    return await cursor.to_list(length=None)


async def channel_exists(channel_id: int):
    channel = await channels.find_one(
        {
            "_id": channel_id
        }
    )

    return channel is not None


async def update_channel(
    channel_id: int,
    data: dict,
):
    data["updated_at"] = datetime.utcnow()

    await channels.update_one(
        {
            "_id": channel_id
        },
        {
            "$set": data
        },
    )


async def disable_channel(channel_id: int):
    await channels.update_one(
        {
            "_id": channel_id
        },
        {
            "$set": {
                "is_active": False,
                "updated_at": datetime.utcnow(),
            }
        },
    )


async def enable_channel(channel_id: int):
    await channels.update_one(
        {
            "_id": channel_id
        },
        {
            "$set": {
                "is_active": True,
                "updated_at": datetime.utcnow(),
            }
        },
    )


async def delete_channel(channel_id: int):
    await channels.delete_one(
        {
            "_id": channel_id
        }
    )


async def total_channels():
    return await channels.count_documents(
        {
            "is_active": True
        }
    )


async def set_invite_link(
    channel_id: int,
    invite_link: str,
):
    await channels.update_one(
        {
            "_id": channel_id
        },
        {
            "$set": {
                "invite_link": invite_link,
                "updated_at": datetime.utcnow(),
            }
        },
    )


async def get_invite_link(channel_id: int):
    channel = await channels.find_one(
        {
            "_id": channel_id
        }
    )

    if not channel:
        return None

    return channel.get("invite_link")


async def clear_invite_link(channel_id: int):
    await channels.update_one(
        {
            "_id": channel_id
        },
        {
            "$unset": {
                "invite_link": ""
            },
            "$set": {
                "updated_at": datetime.utcnow(),
            }
        },
    )
from datetime import datetime
from database.mongo import payments


async def create_payment(
    user_id: int,
    amount: float,
    plan_days: int,
    screenshot_file_id: str = None,
):
    """
    Create a new payment request.
    """

    payment = {
        "user_id": user_id,
        "amount": amount,
        "plan_days": plan_days,
        "status": "pending",      # pending | approved | rejected
        "screenshot_file_id": screenshot_file_id,
        "approved_by": None,
        "rejected_by": None,
        "remark": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    result = await payments.insert_one(payment)

    return str(result.inserted_id)


async def get_payment(payment_id):
    from bson import ObjectId

    return await payments.find_one(
        {
            "_id": ObjectId(payment_id)
        }
    )


async def get_pending_payments():
    cursor = payments.find(
        {
            "status": "pending"
        }
    ).sort("created_at", 1)

    return await cursor.to_list(length=None)


async def approve_payment(
    payment_id,
    admin_id: int,
):
    from bson import ObjectId

    await payments.update_one(
        {
            "_id": ObjectId(payment_id)
        },
        {
            "$set": {
                "status": "approved",
                "approved_by": admin_id,
                "updated_at": datetime.utcnow(),
            }
        },
    )


async def reject_payment(
    payment_id,
    admin_id: int,
    remark: str = None,
):
    from bson import ObjectId

    await payments.update_one(
        {
            "_id": ObjectId(payment_id)
        },
        {
            "$set": {
                "status": "rejected",
                "rejected_by": admin_id,
                "remark": remark,
                "updated_at": datetime.utcnow(),
            }
        },
    )


async def update_screenshot(
    payment_id,
    file_id: str,
):
    from bson import ObjectId

    await payments.update_one(
        {
            "_id": ObjectId(payment_id)
        },
        {
            "$set": {
                "screenshot_file_id": file_id,
                "updated_at": datetime.utcnow(),
            }
        },
    )


async def get_user_payments(
    user_id: int,
):
    cursor = payments.find(
        {
            "user_id": user_id
        }
    ).sort("created_at", -1)

    return await cursor.to_list(length=None)


async def total_revenue():
    pipeline = [
        {
            "$match": {
                "status": "approved"
            }
        },
        {
            "$group": {
                "_id": None,
                "total": {
                    "$sum": "$amount"
                }
            }
        },
    ]

    result = await payments.aggregate(
        pipeline
    ).to_list(length=1)

    if result:
        return result[0]["total"]

    return 0


async def total_payments():
    return await payments.count_documents({})


async def pending_payments_count():
    return await payments.count_documents(
        {
            "status": "pending"
        }
    )


async def approved_payments_count():
    return await payments.count_documents(
        {
            "status": "approved"
        }
    )


async def rejected_payments_count():
    return await payments.count_documents(
        {
            "status": "rejected"
        }
    )
from datetime import datetime, timedelta

from database.mongo import subscriptions


async def create_subscription(
    user_id: int,
    plan_days: int,
    channels: list,
):
    """
    Create new subscription for user.
    """

    expiry_date = datetime.utcnow() + timedelta(days=plan_days)

    data = {
        "user_id": user_id,
        "plan_days": plan_days,
        "channels": channels,
        "is_active": True,
        "start_date": datetime.utcnow(),
        "expiry_date": expiry_date,
        "renew_count": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    await subscriptions.update_one(
        {"user_id": user_id},
        {
            "$set": data
        },
        upsert=True,
    )

    return expiry_date


async def get_subscription(user_id: int):
    return await subscriptions.find_one(
        {"user_id": user_id}
    )


async def activate_subscription(user_id: int):
    await subscriptions.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "is_active": True,
                "updated_at": datetime.utcnow(),
            }
        },
    )


async def deactivate_subscription(user_id: int):
    await subscriptions.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "is_active": False,
                "updated_at": datetime.utcnow(),
            }
        },
    )


async def renew_subscription(
    user_id: int,
    extra_days: int,
):
    sub = await get_subscription(user_id)

    if not sub:
        return None

    current_expiry = sub.get("expiry_date")

    if current_expiry and current_expiry > datetime.utcnow():
        new_expiry = current_expiry + timedelta(days=extra_days)
    else:
        new_expiry = datetime.utcnow() + timedelta(days=extra_days)

    await subscriptions.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "expiry_date": new_expiry,
                "is_active": True,
                "updated_at": datetime.utcnow(),
            },
            "$inc": {
                "renew_count": 1,
            },
        },
    )

    return new_expiry


async def is_subscription_active(user_id: int):
    sub = await get_subscription(user_id)

    if not sub:
        return False

    if not sub.get("is_active"):
        return False

    expiry = sub.get("expiry_date")

    if not expiry:
        return False

    return expiry > datetime.utcnow()


async def get_expired_subscriptions():
    cursor = subscriptions.find(
        {
            "is_active": True,
            "expiry_date": {
                "$lte": datetime.utcnow()
            },
        }
    )

    return await cursor.to_list(length=None)


async def get_active_subscriptions():
    cursor = subscriptions.find(
        {
            "is_active": True,
            "expiry_date": {
                "$gt": datetime.utcnow()
            },
        }
    )

    return await cursor.to_list(length=None)


async def remove_subscription(user_id: int):
    await subscriptions.delete_one(
        {"user_id": user_id}
    )


async def total_subscriptions():
    return await subscriptions.count_documents({})


async def active_subscriptions_count():
    return await subscriptions.count_documents(
        {
            "is_active": True,
            "expiry_date": {
                "$gt": datetime.utcnow()
            },
        }
    )


async def expired_subscriptions_count():
    return await subscriptions.count_documents(
        {
            "expiry_date": {
                "$lte": datetime.utcnow()
            },
        }
    )
