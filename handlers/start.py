from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
import json
import random

from database import create_user, update_goal, get_user
from llm_client import generate_response

router = Router()

class GoalStates(StatesGroup):
    waiting_for_goal = State()

def load_phrases():
    with open("data/phrases.json", "r", encoding="utf-8") as f:
        return json.load(f)

PHRASES = load_phrases()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if user and user.get('goal_text'):
        await message.answer(
            "👋 Ты уже зарегистрирован! Твоя текущая цель:\n"
            f"{user['goal_text']}\n\n"
            "Если хочешь изменить цель — напиши /new_goal"
        )
        return

    # Новый пользователь
    create_user(message.from_user.id, message.from_user.username)
    await message.answer(
        "🏆 *Добро пожаловать в Академию Успеха!*\n\n"
        "Я — *Брайан Хилл-Трейс*, твой персональный коуч с планеты Мотивация.\n"
        "Я помогу тебе превратить твою мечту в реальность через ежедневные ритуалы.\n\n"
        "🎯 *Правило №1:* Чётко сформулируй цель.\n"
        "Не «хочу денег», а «заработаю 10 000$ на продаже кактусов к 1 декабря».\n\n"
        "✍️ *Напиши свою цель прямо сейчас:*",
        parse_mode="Markdown"
    )
    await state.set_state(GoalStates.waiting_for_goal)

@router.message(GoalStates.waiting_for_goal, F.text)
async def set_goal(message: Message, state: FSMContext):
    goal = message.text.strip()
    if len(goal) < 5:
        await message.answer("Слишком коротко! Опиши цель подробнее (минимум 5 символов).")
        return

    update_goal(message.from_user.id, goal)
    await message.answer(
        f"✅ *Цель принята!*\n\n"
        f"«{goal}»\n\n"
        "Теперь каждый день в 8:00 и 20:00 я буду напоминать тебе о ней.\n"
        "Ты будешь повторять её дважды в день — так она проникнет в подсознание.\n\n"
        "🚀 Поехали! Завтра утром жди сообщение.",
        parse_mode="Markdown"
    )
    await state.clear()

@router.message(Command("new_goal"))
async def cmd_new_goal(message: Message, state: FSMContext):
    await message.answer("✍️ Напиши новую цель (она заменит старую):")
    await state.set_state(GoalStates.waiting_for_goal)
