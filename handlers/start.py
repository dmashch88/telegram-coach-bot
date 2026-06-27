import re
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from database import get_user, create_user, update_goal, set_user_timezone
from states import GoalStates
from utils import get_user_timezone_str, get_current_time_in_tz

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if user and user.get('goal_text'):
        await message.answer(
            "Ты уже зарегистрирован! Твоя текущая цель:\n"
            f"{user['goal_text']}\n\n"
            "Чтобы сменить часовой пояс — напиши об этом или используй /settimezone"
        )
        return

    create_user(message.from_user.id, message.from_user.username)
    await message.answer(
        "🌟 *Классно, что ты решил добиться своей цели!*\n\n"
        "Как говорят известные авторы Брайан Трейси или Наполеон Хилл — "
        "нужно чётко сформулировать осязаемую цель и обозначить срок, "
        "в который ты хочешь этого добиться.\n\n"
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
        "Теперь укажи свой *часовой пояс* в формате `+3` или `-5`.\n"
        "Я сверю с текущим временем и настрою напоминания.",
        parse_mode="Markdown"
    )
    await state.set_state(GoalStates.waiting_for_timezone)

@router.message(GoalStates.waiting_for_timezone, F.text)
async def set_timezone(message: Message, state: FSMContext):
    tz_input = message.text.strip()
    if re.match(r"^[+-]\d{1,2}$", tz_input):
        tz_str = get_user_timezone_str(tz_input)
        if tz_str:
            set_user_timezone(message.from_user.id, tz_str)
            current_time = get_current_time_in_tz(tz_str).strftime("%H:%M")
            await message.answer(
                f"✅ Часовой пояс установлен: {tz_input} (UTC{tz_input}).\n"
                f"🕐 Текущее время: {current_time}\n\n"
                "Жду твоего первого сообщения в утреннем окне (6:00–9:00) "
                "или вечернем (21:00–24:00) по твоему времени.\n\n"
                "Напиши *ПОМОЩЬ*, чтобы увидеть список команд.",
                parse_mode="Markdown"
            )
            await state.clear()
            return
    await message.answer(
        "⚠️ Неверный формат. Напиши часовой пояс в формате `+3` или `-5`.",
        parse_mode="Markdown"
    )