from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
import json
import random

from database import create_user, update_goal, get_user, set_user_timezone
from llm_client import generate_response
from utils import validate_timezone, POPULAR_TIMEZONES

router = Router()

class GoalStates(StatesGroup):
    waiting_for_goal = State()
    waiting_for_timezone = State()

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
            "Чтобы сменить часовой пояс — напиши об этом или используй /settimezone"
        )
        return

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
        "Теперь давай настроим твой часовой пояс, чтобы я знал, когда тебя будить.\n"
        "Просто напиши его в формате `Europe/Moscow` или выбери из популярных:\n"
        f"{', '.join(POPULAR_TIMEZONES[:5])}\n"
        "Если не хочешь — напиши `пропустить`.",
        parse_mode="Markdown"
    )
    await state.set_state(GoalStates.waiting_for_timezone)

@router.message(GoalStates.waiting_for_timezone, F.text)
async def set_timezone(message: Message, state: FSMContext):
    tz_input = message.text.strip()
    if tz_input.lower() == "пропустить":
        await message.answer("Хорошо, буду использовать время сервера. "
                             "Ты всегда можешь изменить его командой /settimezone")
        await state.clear()
        return

    if validate_timezone(tz_input):
        set_user_timezone(message.from_user.id, tz_input)
        await message.answer(f"✅ Часовой пояс установлен: {tz_input}.\n"
                             "Теперь каждый день в 8:00 и 20:00 по твоему времени я буду напоминать о цели.")
        await state.clear()
    else:
        await message.answer("⚠️ Неизвестный часовой пояс. Попробуй ещё раз. "
                             "Например: `Europe/Moscow`, `Europe/Berlin`, `America/New_York`.\n"
                             "Или напиши `пропустить`.")
        return

# Команда для смены пояса (оставлена)
@router.message(Command("settimezone"))
async def cmd_settimezone(message: Message, state: FSMContext):
    await message.answer(
        "🕒 Введи новый часовой пояс (например, `Europe/Moscow`):\n"
        f"Популярные: {', '.join(POPULAR_TIMEZONES[:7])}"
    )
    await state.set_state(GoalStates.waiting_for_timezone)