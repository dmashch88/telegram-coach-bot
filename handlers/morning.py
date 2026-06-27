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

@router.message(F.text, lambda m: is_within_window(get_user_timezone(m.from_user.id) or "UTC", "morning"))
async def process_morning_response(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if not user or not user.get('goal_text'):
        await message.answer("Пожалуйста, сначала зарегистрируй цель через /start.")
        return

    goal = user['goal_text']
    user_input = message.text.strip()
    tz = user.get('timezone') or "UTC"
    today = get_today_str(tz)

    # Проверяем, содержит ли сообщение цель (простое сравнение)
    matched = goal.lower() in user_input.lower()
    if not matched:
        await message.answer(
            "❌ Я не увидел твою цель в сообщении. Попробуй ещё раз, напиши её точно!\n\n"
            f"Твоя цель: *{goal}*",
            parse_mode="Markdown"
        )
        return

    # Сохраняем совпадение и обновляем серию
    save_goal_match(user['id'], today, "morning", matched)
    update_streak(user['id'], today)

    # Генерируем мотивирующий ответ
    system_prompt = "Ты вдохновляющий коуч. Поздравь пользователя с тем, что он повторяет свою цель."
    prompt = f"Пользователь повторил свою цель: {goal}. Ответь кратко и вдохновляюще."
    bot_response = await generate_response(prompt, system_prompt)
    if not bot_response:
        bot_response = random.choice(PHRASES.get("praise", ["Отлично! Ты на верном пути!"]))

    # Случайная цитата
    quote = random.choice(QUOTES)

    await message.answer(
        f"{bot_response}\n\n"
        f"📖 *Цитата дня:*\n_{quote}_\n\n"
        "💡 Ты можешь писать в этот чат любые мысли и идеи, которые приблизят тебя к цели. "
        "Я не буду мешать, вернусь к тебе вечером после 21:00.",
        parse_mode="Markdown"
    )

    save_session(user['id'], "morning", user_input, bot_response)
    await state.clear()

    # Проверка юбилея
    await check_anniversary(message, user['id'])

# Функция для отправки утреннего напоминания (используется планировщиком, если нужно)
async def send_morning_message(bot, telegram_id, goal_text):
    # Можно отправить напоминание, но пока не реализуем
    pass