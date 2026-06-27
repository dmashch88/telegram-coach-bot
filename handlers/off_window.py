from aiogram import Router, F
from aiogram.types import Message
from database import get_user
from utils import get_user_timezone, is_within_window
from llm_client import generate_response
import random
from data.phrases import PHRASES

router = Router()

# Этот роутер должен быть зарегистрирован последним, чтобы ловить все остальные сообщения
@router.message(F.text)
async def off_window_message(message: Message):
    user = get_user(message.from_user.id)
    if not user or not user.get('goal_text'):
        await message.answer("Пожалуйста, начни с /start, чтобы зарегистрировать цель.")
        return

    tz = user.get('timezone') or "UTC"
    # Если сообщение вне окон, просто даём случайный ответ или цитату
    if not (is_within_window(tz, "morning") or is_within_window(tz, "evening")):
        # Генерируем вдохновляющий ответ
        prompt = f"Пользователь написал: {message.text}. Ответь кратко, поддерживающе."
        bot_response = await generate_response(prompt, "Ты добрый коуч.")
        if not bot_response:
            bot_response = random.choice(PHRASES.get("off_window", ["Запомни: каждый шаг приближает тебя к цели."]))
        await message.answer(bot_response)