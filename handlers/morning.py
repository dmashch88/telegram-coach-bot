from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
import json
import random
from datetime import datetime

from database import get_user, save_session, get_user_timezone
from llm_client import generate_response
from utils import is_within_window
from config import TIMEZONE as DEFAULT_TZ

router = Router()

class MorningStates(StatesGroup):
    morning_confirm = State()

def load_phrases():
    with open("data/phrases.json", "r", encoding="utf-8") as f:
        return json.load(f)

def load_quotes():
    with open("data/quotes.txt", "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

PHRASES = load_phrases()
QUOTES = load_quotes()

async def send_morning_message(bot, telegram_id: int, goal_text: str):
    """Отправляет утреннее сообщение пользователю"""
    greeting = random.choice(PHRASES["greetings"]["morning"])
    reminder_template = random.choice(PHRASES["goal_reminder"])
    reminder = reminder_template.replace("{goal}", goal_text)
    quote = random.choice(QUOTES)

    text = (
        f"🌅 {greeting}\n\n"
        f"{reminder}\n\n"
        f"📝 *Напиши свою цель снова* (можно скопировать из сообщения выше)\n"
        f"И добавь эмодзи своего настроения: 🔥 если готов к бою, или 🐸 если нужна зарядка.\n\n"
        f"💬 *Цитата дня:*\n_{quote}_"
    )
    await bot.send_message(telegram_id, text, parse_mode="Markdown")

@router.message(F.text, MorningStates.morning_confirm)
async def process_morning_response(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if not user or not user.get('goal_text'):
        await message.answer("У тебя нет активной цели. Напиши /start, чтобы создать её.")
        await state.clear()
        return

    # Определяем часовой пояс пользователя
    tz = get_user_timezone(message.from_user.id) or DEFAULT_TZ

    # Проверяем, попадает ли время в утреннее окно
    if not is_within_window(tz, "morning"):
        r = random.random()
        if r < PHRASES["off_window"]["ignore_chance"]:
            # Игнорируем (не отвечаем)
            pass
        elif r < 0.7:
            await message.answer(PHRASES["off_window"]["dry_response"])
        else:
            quote = random.choice(QUOTES)
            await message.answer(
                PHRASES["off_window"]["with_quote"].replace("{quote}", quote),
                parse_mode="Markdown"
            )
        await state.clear()
        return

    # Стандартная обработка утреннего ответа
    goal = user['goal_text']
    user_input = message.text

    if goal.lower() not in user_input.lower():
        await message.answer(
            "🧐 Я не увидел твою цель в сообщении. Попробуй ещё раз, напиши её точно!"
        )
        return

    system_prompt = "Ты пафосный коуч, хвали пользователя за повторение цели, мотивируй."
    prompt = f"Пользователь только что написал свою цель: {user_input}. Ответь ему кратко и вдохновляюще, используй одну из фраз похвалы."
    bot_response = await generate_response(prompt, system_prompt)
    if not bot_response:
        bot_response = random.choice(PHRASES["praise"])

    await message.answer(f"{bot_response}\n\n🔥 Отличный старт! Иди и властвуй!")
    save_session(user['id'], "morning", user_input, bot_response)
    await state.clear()