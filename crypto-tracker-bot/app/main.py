import asyncio
import logging
import os
from dataclasses import dataclass

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv

from app.bot.handlers import setup_routers
from app.db.database import Database
from app.scheduler import create_scheduler
from app.services.coingecko import CoinGeckoClient


@dataclass(frozen=True, slots=True)
class Settings:
    bot_token: str
    database_url: str
    alert_interval_minutes: int
    coingecko_base_url: str

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        bot_token = os.getenv("BOT_TOKEN", "").strip()
        if not bot_token:
            raise RuntimeError("BOT_TOKEN is required.")

        return cls(
            bot_token=bot_token,
            database_url=os.getenv("DATABASE_URL", "data/crypto_tracker.sqlite3"),
            alert_interval_minutes=max(
                1,
                int(os.getenv("ALERT_INTERVAL_MINUTES", "5")),
            ),
            coingecko_base_url=os.getenv(
                "COINGECKO_BASE_URL",
                "https://api.coingecko.com/api/v3",
            ),
        )


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = Settings.from_env()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    db = Database(settings.database_url)
    coingecko = CoinGeckoClient(settings.coingecko_base_url)
    scheduler = create_scheduler(
        bot=bot,
        db=db,
        coingecko=coingecko,
        interval_minutes=settings.alert_interval_minutes,
    )

    await db.connect()
    await db.init()
    await coingecko.connect()

    dp["db"] = db
    dp["coingecko"] = coingecko
    dp.include_router(setup_routers())
    scheduler.start()

    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await coingecko.close()
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
