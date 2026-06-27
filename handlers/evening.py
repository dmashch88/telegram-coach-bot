import random
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database import get_user, save_session, update_streak, save_goal_match, get_user_timezone
from utils import get_today_str, is_within_window
from llm_client import generate_response
from handlers.stats import check_anniversary
from data.phrases import PHRASES
from data.quotes import QUOTES

router = Router()

@router.message(F.text, lambda m: is_within_window(get_user_timezone(m.from_user.id) or "UTC", "evening"))
async def process_evening_response(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if not user or not user.get('goal_text'):
        await message.answer("Пожалуйста, сначала зарегистрируй цель через /start.")
        return

    goal = user['goal_text']
    user_input = message.text.strip()
    tz = user.get('timezone') or "UTC"
    today = get_today_str(tz)

    # Проверяем, содержит ли сообщение цель
    matched = goal.lower() in user_input.lower()
    if not matched:
        await message.answer(
            "❌ Я не увидел твою цель в сообщении. Попробуй ещё раз, напиши её точно!\n\n"
            f"Твоя цель: *{goal}*",
            parse_mode="Markdown"
        )
        return

    save_goal_match(user['id'], today, "evening", matched)
    update_streak(user['id'], today)

    # Генерируем ответ на отчёт о шагах
    system_prompt = "Ты коуч. Отреагируй на отчёт пользователя о шаге к цели."
    prompt = f"Пользователь написал: {user_input}. Ответь кратко и мотивирующе."
    bot_response = await generate_response(prompt, system_prompt)
    if not bot_response:
        if "прокрастинировал" in user_input.lower():
            bot_response = random.choice(PHRASES.get("scold", ["Не сдавайся! Завтра новый день."]))
        else:
            bot_response = random.choice(PHRASES.get("praise", ["Отлично! Ты сделал шаг вперёд!"]))

    await message.answer(
        f"{bot_response}\n\n"
        "🌙 Отличная работа над собой! Спокойной ночи, завтра новый день.",
        parse_mode="Markdown"
    )

    save_session(user['id'], "evening", user_input, bot_response)
    await state.clear()

    await check_anniversary(message, user['id'])

async def send_evening_message(bot, telegram_id, goal_text):
    pass