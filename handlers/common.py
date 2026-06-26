from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
import random

from database import get_stats, get_user

router = Router()

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
