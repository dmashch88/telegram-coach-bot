from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
import random
from datetime import datetime

from database import get_user, get_user_timezone
from utils import is_within_window, get_next_window_info
from config import TIMEZONE as DEFAULT_TZ

router = Router()

class OffWindow(StatesGroup):
    tracking = State()  # состояние, когда считаем попытки

def load_quotes():
    with open("data/quotes.txt", "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

QUOTES = load_quotes()

def load_phrases():
    import json
    with open("data/phrases.json", "r", encoding="utf-8") as f:
        return json.load(f)

PHRASES = load_phrases()

@router.message(F.text, ~F.text.startswith("/"))  # не команды
async def handle_off_window(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if not user or not user.get('goal_text'):
        # Нет цели – игнорируем
        return

    tz = get_user_timezone(message.from_user.id) or DEFAULT_TZ
    current_state = await state.get_state()

    # Если пользователь уже в процессе утреннего/вечернего подтверждения, не мешаем
    if current_state and ("MorningStates" in current_state or "EveningStates" in current_state):
        return

    # Проверяем окна
    if is_within_window(tz, "morning") or is_within_window(tz, "evening"):
        # Внутри окна – передаём управление другим обработчикам (утреннему/вечернему)
        # Сбрасываем счётчик, если был
        if current_state == OffWindow.tracking:
            await state.clear()
        return

    # --- Вне окна ---
    data = await state.get_data()
    count = data.get("off_count", 0)

    if count == 0:
        # Первое сообщение – предупреждение
        await message.answer(PHRASES["off_window"]["dry_response"])
        count += 1
    elif count == 1:
        # Второе – игнор (ничего не отправляем)
        count += 1
    else:
        # Третье и далее – цитата + информация о следующем окне
        next_info = get_next_window_info(tz)
        if next_info:
            window_name, time_left = next_info
            quote = random.choice(QUOTES)
            window_label = "утро (6:00)" if window_name == "morning" else "вечер (21:00)"
            await message.answer(
                f"💬 *Цитата:* _{quote}_\n\n"
                f"Возвращайся в своё окно – {window_label} (через {time_left}). "
                "А пока сосредоточься на цели!",
                parse_mode="Markdown"
            )
        count = 0  # сбрасываем счётчик после третьего

    await state.set_data({"off_count": count})
    await state.set_state(OffWindow.tracking)