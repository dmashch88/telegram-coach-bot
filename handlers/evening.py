from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
import json
import random

from database import get_user, save_session
from llm_client import generate_response

router = Router()

class EveningStates(StatesGroup):
    evening_report = State()

def load_phrases():
    with open("data/phrases.json", "r", encoding="utf-8") as f:
        return json.load(f)

PHRASES = load_phrases()

async def send_evening_message(bot, telegram_id: int, goal_text: str):
    greeting = random.choice(PHRASES["greetings"]["evening"])
    reminder_template = random.choice(PHRASES["goal_reminder"])
    reminder = reminder_template.replace("{goal}", goal_text)
    text = (
        f"🌆 {greeting}\n\n"
        f"{reminder}\n\n"
        f"📝 *Напиши свою цель ещё раз* для закрепления.\n"
        f"Затем ответь на вопрос: *Какой 1 шаг ты сделал сегодня к этой цели?*\n"
        f"Если не сделал — напиши «ПРОКРАСТИНИРОВАЛ».\n\n"
        f"Будь честен, это твой личный дневник."
    )
    await bot.send_message(telegram_id, text, parse_mode="Markdown")

@router.message(F.text, EveningStates.evening_report)
async def process_evening_response(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("Ты не зарегистрирован. Напиши /start.")
        await state.clear()
        return

    user_input = message.text
    goal = user['goal_text']

    if goal.lower() not in user_input.lower():
        await message.answer(
            "🧐 Я не вижу твою цель в сообщении. Напиши её ещё раз вместе с шагом."
        )
        return

    if "прокрастинировал" in user_input.lower():
        bot_response = random.choice(PHRASES["scold"])
    else:
        bot_response = random.choice(PHRASES["praise"])

    system_prompt = "Ты коуч. Отреагируй на отчёт пользователя о шаге. Если шаг сделан — похвали, если нет — мягко подбодри."
    prompt = f"Пользователь написал: {user_input}. Ответь кратко и мотивирующе."
    llm_response = await generate_response(prompt, system_prompt)
    if llm_response:
        bot_response = llm_response

    await message.answer(
        f"{bot_response}\n\n"
        f"💪 Отличная работа над собой! Спокойной ночи, завтра новый день."
    )
    save_session(user['id'], "evening", user_input, bot_response)
    await state.clear()
