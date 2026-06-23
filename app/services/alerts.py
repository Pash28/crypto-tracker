import logging
from decimal import Decimal

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from app.bot.keyboards import alert_triggered_text
from app.db.database import Database, DatabaseError
from app.db.models import Alert
from app.services.coingecko import CoinGeckoAPIError, CoinGeckoClient

logger = logging.getLogger(__name__)


async def check_price_alerts(
    bot: Bot,
    db: Database,
    coingecko: CoinGeckoClient,
) -> None:
    try:
        alerts = await db.get_active_alerts()
    except DatabaseError:
        logger.exception("Could not load active alerts")
        return

    coin_ids = {alert.coin_id for alert in alerts}
    if not coin_ids:
        return

    try:
        prices = await coingecko.get_prices_by_coin_ids(coin_ids)
    except CoinGeckoAPIError:
        logger.exception("Could not fetch prices for alert monitoring")
        return

    for alert in alerts:
        current_price = prices.get(alert.coin_id)
        if current_price is None or not _is_triggered(alert, current_price):
            continue

        try:
            await bot.send_message(
                chat_id=alert.user_id,
                text=alert_triggered_text(alert, current_price),
            )
            await db.deactivate_alert(alert.id)
        except TelegramAPIError:
            logger.exception("Could not notify user for alert %s", alert.id)
        except DatabaseError:
            logger.exception("Could not deactivate alert %s", alert.id)


def _is_triggered(alert: Alert, current_price: Decimal) -> bool:
    if alert.direction == "above":
        return current_price >= alert.target_price
    return current_price <= alert.target_price
