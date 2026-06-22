from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import error_text, top_text
from app.services.coingecko import CoinGeckoAPIError, CoinGeckoClient

router = Router(name="market")


@router.message(Command("top"))
async def top_command(message: Message, coingecko: CoinGeckoClient) -> None:
    try:
        coins = await coingecko.get_top_coins(limit=10)
    except CoinGeckoAPIError as exc:
        await message.answer(error_text(str(exc)))
        return

    await message.answer(top_text(coins))


@router.callback_query(lambda callback: callback.data == "show_top")
async def top_callback(callback: CallbackQuery, coingecko: CoinGeckoClient) -> None:
    try:
        coins = await coingecko.get_top_coins(limit=10)
    except CoinGeckoAPIError as exc:
        await callback.message.answer(error_text(str(exc)))
        await callback.answer()
        return

    await callback.message.answer(top_text(coins))
    await callback.answer()
