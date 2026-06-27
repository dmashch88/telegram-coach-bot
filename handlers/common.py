from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from database import get_user, delete_user_data, set_user_timezone, get_user_timezone
from utils import get_user_timezone_str, get_current_time_in_tz
import re

router = Router()

@router.message(Command("reset"))
async def cmd_reset(message: Message):
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("Ты ещё не зарегистрирован.")
        return
    delete_user_data(message.from_user.id)
    await message.answer(
        "🔄 Все твои данные удалены. Чтобы начать заново, напиши /start."
    )

# Обработчик для команды "Перезагрузка" (русский вариант)
@router.message(F.text.lower() == "перезагрузка")
async def cmd_reset_ru(message: Message):
    await cmd_reset(message)

@router.message(Command("settimezone"))
@router.message(F.text.lower().startswith("часовой пояс"))
async def cmd_set_timezone(message: Message):
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала зарегистрируйся через /start.")
        return
    # Извлекаем часовой пояс из текста
    text = message.text.lower()
    # Если команда /settimezone, то нужно прочитать следующий аргумент
    if text.startswith("/settimezone"):
        parts = text.split()
        if len(parts) > 1:
            tz_input = parts[1]
        else:
            await message.answer("Напиши часовой пояс в формате `+3` или `-5` после команды.\nПример: `/settimezone +3`", parse_mode="Markdown")
            return
    else:
        # "часовой пояс +3"
        match = re.search(r"[+-]\d{1,2}", text)
        if match:
            tz_input = match.group()
        else:
            await message.answer("Напиши часовой пояс в формате `+3` или `-5`.\nПример: `часовой пояс +3`", parse_mode="Markdown")
            return

    if re.match(r"^[+-]\d{1,2}$", tz_input):
        tz_str = get_user_timezone_str(tz_input)
        if tz_str:
            set_user_timezone(message.from_user.id, tz_str)
            current_time = get_current_time_in_tz(tz_str).strftime("%H:%M")
            await message.answer(
                f"✅ Часовой пояс обновлён на {tz_input} (UTC{tz_input}).\n"
                f"🕐 Текущее время: {current_time}",
                parse_mode="Markdown"
            )
            return
    await message.answer("⚠️ Неверный формат. Используй `+3` или `-5`.", parse_mode="Markdown")