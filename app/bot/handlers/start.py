from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.bot.keyboards import command_keyboard, error_text, welcome_text
from app.db.database import Database, DatabaseError

router = Router(name="start")


@router.message(CommandStart())
async def start_command(message: Message, db: Database) -> None:
    try:
        await db.upsert_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )
    except DatabaseError as exc:
        await message.answer(error_text(str(exc)))
        return

    await message.answer(welcome_text(), reply_markup=command_keyboard())
