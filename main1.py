#!/usr/bin/env python3
import asyncio
import json
import logging
import sqlite3
import random
from datetime import datetime, timedelta
from contextlib import closing

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz

# ===================== НАСТРОЙКИ =====================
BOT_TOKEN = 8990565741:AAFlbc9JVkkM63A7lkuYAvD01sxW5EiLpOU   # замените на реальный токен
DB_NAME = 'coach_bot.db'
PHRASES_FILE = 'data/phrases.json'   # путь к файлу с фразами

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===================== ЗАГРУЗКА ФРАЗ =====================
def load_phrases():
    try:
        with open(PHRASES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Файл {PHRASES_FILE} не найден, использую стандартные фразы.")
        return {
            "greetings": {"morning": ["Доброе утро!"], "evening": ["Добрый вечер!"]},
            "praise": ["Отлично!"],
            "scold": ["Ничего страшного."],
            "goal_reminder": ["Ваша цель — {goal}."],
            "off_window": {
                "dry_response": "⏰ Сейчас не время.",
                "with_quote": "💬 Цитата: {quote}"
            }
        }

PHRASES = load_phrases()

# ===================== СОСТОЯНИЯ FSM =====================
class GoalStates(StatesGroup):
    waiting_for_goal = State()
    waiting_for_confirm = State()

class TimezoneStates(StatesGroup):
    waiting_for_timezone = State()

# ===================== РАБОТА С БАЗОЙ ДАННЫХ =====================
def init_db():
    with closing(sqlite3.connect(DB_NAME)) as conn:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                goal TEXT,
                timezone_offset INTEGER DEFAULT 0,
                last_yes_date TEXT,
                total_yes INTEGER DEFAULT 0,
                streak INTEGER DEFAULT 0,
                awaiting_response INTEGER DEFAULT 0
            )
        ''')
        conn.commit()

def get_user(user_id: int):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        cur = conn.cursor()
        cur.execute('SELECT goal, timezone_offset, last_yes_date, total_yes, streak, awaiting_response FROM users WHERE user_id = ?', (user_id,))
        row = cur.fetchone()
        if row:
            return {
                'goal': row[0],
                'timezone_offset': row[1],
                'last_yes_date': row[2],
                'total_yes': row[3],
                'streak': row[4],
                'awaiting_response': row[5]
            }
        return None

def create_user(user_id: int):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        cur = conn.cursor()
        cur.execute('INSERT OR IGNORE INTO users (user_id, timezone_offset) VALUES (?, ?)', (user_id, 0))
        conn.commit()

def update_user(user_id: int, goal: str = None, timezone_offset: int = None,
                last_yes_date: str = None, total_yes: int = None, streak: int = None,
                awaiting_response: int = None):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        cur = conn.cursor()
        fields = []
        values = []
        if goal is not None:
            fields.append('goal = ?')
            values.append(goal)
        if timezone_offset is not None:
            fields.append('timezone_offset = ?')
            values.append(timezone_offset)
        if last_yes_date is not None:
            fields.append('last_yes_date = ?')
            values.append(last_yes_date)
        if total_yes is not None:
            fields.append('total_yes = ?')
            values.append(total_yes)
        if streak is not None:
            fields.append('streak = ?')
            values.append(streak)
        if awaiting_response is not None:
            fields.append('awaiting_response = ?')
            values.append(awaiting_response)
        if fields:
            values.append(user_id)
            sql = f'UPDATE users SET {", ".join(fields)} WHERE user_id = ?'
            cur.execute(sql, values)
            conn.commit()

# ===================== ОСНОВНЫЕ ОБРАБОТЧИКИ =====================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
scheduler = AsyncIOScheduler()

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    create_user(user_id)
    await state.clear()
    greeting = random.choice([
        "Привет! Я твой персональный коуч по достижению целей.",
        "Здравствуй! Давай начнём путь к твоей мечте.",
        "Рад приветствовать тебя! Я помогу тебе не сбиваться с курса."
    ])
    user = get_user(user_id)
    if user and user['goal']:
        await message.answer(
            f"{greeting}\n\n"
            f"Твоя текущая цель: {user['goal']}\n"
            f"Нажми /setgoal, чтобы изменить цель.\n"
            f"Нажми /settimezone, чтобы настроить часовой пояс.\n"
            f"Каждый день в 9:00 и 21:00 я буду напоминать тебе повторить цель."
        )
    else:
        await message.answer(
            f"{greeting}\n\n"
            "Для начала установи свою главную цель командой /setgoal <текст цели>.\n"
            "Также рекомендую установить часовой пояс командой /settimezone (например, +3)."
        )

@dp.message(Command("setgoal"))
async def cmd_setgoal(message: Message, state: FSMContext):
    user_id = message.from_user.id
    create_user(user_id)
    text = message.text[len('/setgoal '):].strip()
    if text:
        update_user(user_id, goal=text)
        await message.answer(f"Цель установлена: {text}\n\nОтлично! Теперь каждый день подтверждай её /yes или /no.")
        await state.clear()
    else:
        await state.set_state(GoalStates.waiting_for_goal)
        await message.answer("Напиши свою главную цель (текст).")

@dp.message(StateFilter(GoalStates.waiting_for_goal))
async def process_goal_input(message: Message, state: FSMContext):
    user_id = message.from_user.id
    goal = message.text.strip()
    if not goal:
        await message.answer("Цель не может быть пустой. Напиши что-то.")
        return
    update_user(user_id, goal=goal)
    await message.answer(f"Цель сохранена: {goal}\n\nТеперь каждый день подтверждай её /yes или /no.")
    await state.clear()

@dp.message(Command("settimezone"))
async def cmd_settimezone(message: Message, state: FSMContext):
    await state.set_state(TimezoneStates.waiting_for_timezone)
    await message.answer(
        "Укажи свой часовой пояс в формате UTC (например: +3, -5, +03:00).\n"
        "Отправь число с плюсом или минусом."
    )

@dp.message(StateFilter(TimezoneStates.waiting_for_timezone))
async def process_timezone_input(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text.strip().replace('UTC', '').strip()
    try:
        if text.startswith('+') or text.startswith('-'):
            offset_hours = int(text.split(':')[0])
        else:
            offset_hours = int(text)
        if offset_hours < -12 or offset_hours > 14:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число от -12 до +14, например: +3 или -5.")
        return

    update_user(user_id, timezone_offset=offset_hours)

    tz = pytz.FixedOffset(offset_hours * 60)
    now = datetime.now(tz)
    current_time = now.strftime("%H:%M")

    morning = now.replace(hour=9, minute=0, second=0, microsecond=0)
    evening = now.replace(hour=21, minute=0, second=0, microsecond=0)
    if morning < now:
        morning += timedelta(days=1)
    if evening < now:
        evening += timedelta(days=1)
    next_time = min(morning, evening)
    delta = next_time - now
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60

    await message.answer(
        f"Часовой пояс установлен: UTC{offset_hours:+d}\n"
        f"Текущее время по твоему поясу: {current_time}\n"
        f"Ближайшее напоминание (в 9:00 или 21:00) через {hours} ч {minutes} мин.\n"
        f"Я буду напоминать тебе о цели в эти часы."
    )
    await state.clear()

@dp.message(Command("yes"))
async def cmd_yes(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user = get_user(user_id)
    if not user or not user['goal']:
        await message.answer("У тебя ещё нет цели. Установи её /setgoal.")
        return
    today_str = datetime.now().strftime("%Y-%m-%d")
    if user['last_yes_date'] == today_str:
        await message.answer("Ты уже сегодня отметил(а) повторение цели. Молодец!")
        update_user(user_id, awaiting_response=0)
        return
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    if user['last_yes_date'] == yesterday:
        new_streak = user['streak'] + 1
    else:
        new_streak = 1
    new_total = user['total_yes'] + 1
    update_user(user_id, last_yes_date=today_str, total_yes=new_total, streak=new_streak, awaiting_response=0)
    praise_list = PHRASES.get('praise', ["Отлично!"])
    praise = random.choice(praise_list)
    await message.answer(f"{praise}\n\nПродолжай в том же духе! Завтра снова жду подтверждения.")
    await state.clear()

@dp.message(Command("no"))
async def cmd_no(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user = get_user(user_id)
    if not user or not user['goal']:
        await message.answer("У тебя ещё нет цели. Установи её /setgoal.")
        return
    update_user(user_id, streak=0, awaiting_response=0)
    scold_list = PHRASES.get('scold', ["Ничего страшного, завтра будет новый день."])
    scold = random.choice(scold_list)
    await message.answer(f"{scold}\n\nЗавтра не забывай повторить цель!")
    await state.clear()

@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    user_id = message.from_user.id
    user = get_user(user_id)
    if not user:
        await message.answer("Ты ещё не зарегистрирован. Напиши /start.")
        return
    goal = user['goal'] or "не установлена"
    total = user['total_yes']
    streak = user['streak']
    last = user['last_yes_date'] or "никогда"
    await message.answer(
        f"📊 Твоя статистика:\n"
        f"Цель: {goal}\n"
        f"Всего подтверждений: {total}\n"
        f"Дней подряд: {streak}\n"
        f"Последнее подтверждение: {last}"
    )

# ===================== ОБРАБОТКА НЕИЗВЕСТНЫХ СООБЩЕНИЙ =====================
@dp.message(StateFilter(GoalStates.waiting_for_goal))
async def unknown_in_goal_state(message: Message):
    await message.answer("Напиши текст своей цели.")

@dp.message(StateFilter(TimezoneStates.waiting_for_timezone))
async def unknown_in_timezone_state(message: Message):
    await message.answer("Отправь число от -12 до +14, например +3 или -5.")

# Универсальный хендлер для любых других сообщений
@dp.message()
async def handle_any_message(message: Message):
    user_id = message.from_user.id
    user = get_user(user_id)
    if user and user.get('awaiting_response') == 1:
        await message.answer(
            "Я жду твоего ответа: нажми /yes, если ты повторил(а) цель сегодня, или /no, если нет."
        )
    else:
        await message.answer(
            "Используй команды:\n"
            "/setgoal – установить цель\n"
            "/settimezone – настроить часовой пояс\n"
            "/yes – подтвердить цель\n"
            "/no – отказаться\n"
            "/stats – статистика"
        )

# ===================== ФОНОВЫЙ ПЛАНИРОВЩИК НАПОМИНАНИЙ =====================
async def check_reminders():
    now_utc = datetime.utcnow()
    with closing(sqlite3.connect(DB_NAME)) as conn:
        cur = conn.cursor()
        cur.execute('SELECT user_id, goal, timezone_offset, awaiting_response FROM users WHERE goal IS NOT NULL')
        rows = cur.fetchall()
        for user_id, goal, offset, awaiting in rows:
            local_time = now_utc + timedelta(hours=offset)
            hour = local_time.hour
            minute = local_time.minute
            if (hour == 9 or hour == 21) and minute == 0:
                user_data = get_user(user_id)
                if user_data['last_yes_date'] == datetime.now().strftime("%Y-%m-%d"):
                    continue
                if awaiting == 1:
                    continue
                if hour == 9:
                    greeting_list = PHRASES['greetings']['morning']
                else:
                    greeting_list = PHRASES['greetings']['evening']
                greeting = random.choice(greeting_list)
                reminder = random.choice(PHRASES['goal_reminder']).format(goal=goal)
                try:
                    await bot.send_message(
                        user_id,
                        f"{greeting}\n\n{reminder}\n\nТы сегодня повторил(а) свою цель? Нажми /yes или /no."
                    )
                    update_user(user_id, awaiting_response=1)
                except Exception as e:
                    logger.error(f"Не удалось отправить напоминание пользователю {user_id}: {e}")

scheduler.add_job(check_reminders, 'interval', minutes=1)
scheduler.start()

# ===================== ЗАПУСК БОТА =====================
async def main():
    init_db()
    logger.info("Бот запущен")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())