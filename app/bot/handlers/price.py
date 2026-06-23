from aiogram import Router
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from aiogram.types import Message

from app.bot.keyboards import error_text, price_text, usage_text
from app.services.coingecko import CoinGeckoAPIError, CoinGeckoClient, CoinNotFoundError

router = Router(name="price")


@router.message(Command("price"))
async def price_command(
    message: Message,
    command: CommandObject,
    coingecko: CoinGeckoClient,
) -> None:
    ticker = (command.args or "").strip().upper()
    if not ticker:
        await message.answer(usage_text("/price BTC"))
        return

    try:
        coin = await coingecko.get_coin_price(ticker)
    except CoinNotFoundError:
        await message.answer(error_text(f"Unknown ticker: {ticker}"))
        return
    except CoinGeckoAPIError as exc:
        await message.answer(error_text(str(exc)))
        return

    await message.answer(price_text(coin))
