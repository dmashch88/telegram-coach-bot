from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
import random

from database import get_stats, get_user, reset_user, get_user_timezone, set_user_timezone
from utils import POPULAR_TIMEZONES, validate_timezone
from config import TIMEZONE as DEFAULT_TZ

router = Router()

class MiscStates(StatesGroup):
    reset_confirm = State()
    timezone_change_pending = State()

def load_quotes():
    with open("data/quotes.txt", "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

QUOTES = load_quotes()

@router.message(Command("quote"))
async def cmd_quote(message: Message):
    quote = random.choice(QUOTES)
    await message.answer(f"📖 *Цитата дня:*\n_{quote}_", parse_mode="Markdown")

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("Ты ещё не зарегистрирован. Напиши /start.")
        return
    stats = get_stats(message.from_user.id)
    text = (
        f"📊 *Твоя статистика*\n\n"
        f"Утренних сессий: {stats.get('morning', 0)}\n"
        f"Вечерних сессий: {stats.get('evening', 0)}\n"
        f"Всего повторений цели: {stats.get('morning', 0) + stats.get('evening', 0)}\n\n"
        f"Продолжай в том же духе!"
    )
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("reset"))
async def cmd_reset(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("Ты ещё не зарегистрирован. Напиши /start.")
        return
    await message.answer(
        "⚠️ Ты уверен, что хочешь сбросить все данные?\n"
        "Это удалит твою цель, историю, часовой пояс. Ты начнёшь с чистого листа.\n"
        "Напиши `да` для подтверждения."
    )
    await state.set_state(MiscStates.reset_confirm)

@router.message(F.text.lower() == "да", StateFilter(MiscStates.reset_confirm))
async def process_reset_confirm(message: Message, state: FSMContext):
    reset_user(message.from_user.id)
    await message.answer("♻️ Все данные удалены. Давай начнём заново с /start")
    await state.clear()

# Обработчик фраз о часовом поясе вне состояний
@router.message(F.text, StateFilter(None))
async def handle_timezone_request(message: Message, state: FSMContext):
    text = message.text.lower()
    if any(word in text for word in ["часовой пояс", "таймзона", "сменить время", "поменять пояс", "set timezone"]):
        tz = get_user_timezone(message.from_user.id)
        if not tz:
            tz = DEFAULT_TZ
        await message.answer(
            f"🕒 Твой текущий часовой пояс: {tz}.\n"
            "Хочешь изменить? Напиши новый пояс (например, `Europe/Moscow`)"
        )
        await state.set_state(MiscStates.timezone_change_pending)
        return
    # Если не о часовом поясе – ничего не делаем, сообщение уйдёт в off_window

# Обработчик ввода нового часового пояса
@router.message(StateFilter(MiscStates.timezone_change_pending))
async def process_timezone_change(message: Message, state: FSMContext):
    tz_input = message.text.strip()
    if validate_timezone(tz_input):
        set_user_timezone(message.from_user.id, tz_input)
        await message.answer(f"✅ Часовой пояс изменён на {tz_input}.")
        await state.clear()
    else:
        await message.answer("⚠️ Неизвестный часовой пояс. Попробуй ещё раз или напиши /settimezone.")