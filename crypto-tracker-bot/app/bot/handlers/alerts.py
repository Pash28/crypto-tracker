from decimal import Decimal, InvalidOperation

from aiogram import Router
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import alerts_text, error_text, success_text, usage_text
from app.db.database import Database, DatabaseError
from app.services.coingecko import CoinGeckoAPIError, CoinGeckoClient, CoinNotFoundError

router = Router(name="alerts")


@router.message(Command("alert"))
async def create_alert_command(
    message: Message,
    command: CommandObject,
    db: Database,
    coingecko: CoinGeckoClient,
) -> None:
    parts = (command.args or "").split()
    if len(parts) != 3 or parts[1].lower() not in {"above", "below"}:
        await message.answer(usage_text("/alert BTC above 70000"))
        return

    ticker = parts[0].upper()
    direction = parts[1].lower()
    try:
        target_price = Decimal(parts[2])
    except InvalidOperation:
        await message.answer(error_text("Alert price must be a valid number."))
        return

    if target_price <= 0:
        await message.answer(error_text("Alert price must be greater than zero."))
        return

    try:
        coin = await coingecko.resolve_coin(ticker)
    except CoinNotFoundError:
        await message.answer(error_text(f"Unknown ticker: {ticker}"))
        return
    except CoinGeckoAPIError as exc:
        await message.answer(error_text(str(exc)))
        return

    try:
        await db.upsert_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )
        alert_id = await db.create_alert(
            user_id=message.from_user.id,
            ticker=coin.symbol,
            coin_id=coin.id,
            direction=direction,
            target_price=target_price,
        )
    except DatabaseError as exc:
        await message.answer(error_text(str(exc)))
        return

    await message.answer(
        success_text(
            f"Alert #{alert_id} created: {coin.symbol} {direction} ${target_price:,.2f}"
        )
    )


@router.message(Command("alerts"))
async def list_alerts_command(message: Message, db: Database) -> None:
    try:
        rows = await db.list_user_alerts(message.from_user.id)
    except DatabaseError as exc:
        await message.answer(error_text(str(exc)))
        return

    await message.answer(alerts_text(rows))


@router.message(Command("delete"))
async def delete_alert_command(
    message: Message,
    command: CommandObject,
    db: Database,
) -> None:
    raw_alert_id = (command.args or "").strip()
    if not raw_alert_id.isdigit():
        await message.answer(usage_text("/delete 12"))
        return

    try:
        deleted = await db.delete_alert(
            alert_id=int(raw_alert_id),
            user_id=message.from_user.id,
        )
    except DatabaseError as exc:
        await message.answer(error_text(str(exc)))
        return

    if not deleted:
        await message.answer(error_text("Alert not found or already inactive."))
        return

    await message.answer(success_text(f"Alert #{raw_alert_id} deleted."))


@router.callback_query(lambda callback: callback.data == "show_alerts")
async def alerts_callback(callback: CallbackQuery, db: Database) -> None:
    try:
        rows = await db.list_user_alerts(callback.from_user.id)
    except DatabaseError as exc:
        await callback.message.answer(error_text(str(exc)))
        await callback.answer()
        return

    await callback.message.answer(alerts_text(rows))
    await callback.answer()
