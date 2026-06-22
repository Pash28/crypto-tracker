from decimal import Decimal
from html import escape

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.db.models import Alert
from app.services.coingecko import CoinMarketData, CoinPrice


def command_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Top 10", callback_data="show_top"),
                InlineKeyboardButton(text="My alerts", callback_data="show_alerts"),
            ],
        ]
    )


def welcome_text() -> str:
    return (
        "<b>CryptoTracker</b>\n\n"
        "Track crypto prices and create Telegram price alerts.\n\n"
        "<b>Commands</b>\n"
        "/price BTC - current coin price\n"
        "/alert BTC above 70000 - alert when price rises above target\n"
        "/alert ETH below 2000 - alert when price drops below target\n"
        "/alerts - active alerts\n"
        "/delete 12 - delete alert by ID\n"
        "/top - top 10 by market capitalization"
    )


def usage_text(example: str) -> str:
    return f"Usage: <code>{escape(example)}</code>"


def success_text(message: str) -> str:
    return f"Done. {escape(message)}"


def error_text(message: str) -> str:
    return f"Sorry, {escape(message)}"


def price_text(coin: CoinPrice) -> str:
    change = ""
    if coin.change_24h is not None:
        sign = "+" if coin.change_24h >= 0 else ""
        change = f"\n24h: <b>{sign}{coin.change_24h:.2f}%</b>"

    return (
        f"<b>{escape(coin.name)} ({escape(coin.symbol)})</b>\n"
        f"Price: <b>${coin.price_usd:,.8f}</b>{change}"
    )


def alerts_text(alerts: list[Alert]) -> str:
    if not alerts:
        return "You do not have active alerts."

    lines = ["<b>Active alerts</b>"]
    for alert in alerts:
        lines.append(
            f"#{alert.id}: <b>{escape(alert.ticker)}</b> "
            f"{escape(alert.direction)} ${alert.target_price:,.2f}"
        )
    return "\n".join(lines)


def top_text(coins: list[CoinMarketData]) -> str:
    lines = ["<b>Top 10 cryptocurrencies by market cap</b>"]
    for coin in coins:
        market_cap = _format_money(coin.market_cap_usd)
        lines.append(
            f"{coin.rank}. <b>{escape(coin.name)} ({escape(coin.symbol)})</b> "
            f"${coin.price_usd:,.4f} - {market_cap}"
        )
    return "\n".join(lines)


def alert_triggered_text(alert: Alert, price: Decimal) -> str:
    return (
        f"<b>Price alert triggered</b>\n"
        f"Alert #{alert.id}: {escape(alert.ticker)} {escape(alert.direction)} "
        f"${alert.target_price:,.2f}\n"
        f"Current price: <b>${price:,.8f}</b>"
    )


def _format_money(value: Decimal | None) -> str:
    if value is None:
        return "market cap unavailable"
    if value >= Decimal("1000000000000"):
        return f"${value / Decimal('1000000000000'):.2f}T"
    if value >= Decimal("1000000000"):
        return f"${value / Decimal('1000000000'):.2f}B"
    if value >= Decimal("1000000"):
        return f"${value / Decimal('1000000'):.2f}M"
    return f"${value:,.0f}"
