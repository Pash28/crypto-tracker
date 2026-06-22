from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

from app.db.database import Database
from app.services.alerts import check_price_alerts
from app.services.coingecko import CoinGeckoClient


def create_scheduler(
    bot: Bot,
    db: Database,
    coingecko: CoinGeckoClient,
    interval_minutes: int,
) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        check_price_alerts,
        trigger="interval",
        minutes=interval_minutes,
        kwargs={"bot": bot, "db": db, "coingecko": coingecko},
        id="price_alert_monitor",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    return scheduler
