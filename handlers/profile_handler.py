from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from states.profile_states import ProfileStates
from keyboards.inline_keyboards import utc_selection_keyboard
from database import get_user, update_profile, set_utc_offset, get_utc_offset

router = Router()

# Команда /profile – показывает текущие данные и предлагает изменить
@router.message(Command("profile"))
async def show_profile(message: types.Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала зарегистрируйтесь через /start")
        return

    _, username, first, last, age, weight, height, goal, utc = user
    text = (
        f"👤 Профиль\n"
        f"Имя: {first or '—'}\n"
        f"Возраст: {age or '—'}\n"
        f"Вес: {weight or '—'} кг\n"
        f"Рост: {height or '—'} см\n"
        f"Цель: {goal or '—'}\n"
        f"Часовой пояс: UTC{utc:+} (смещение в часах)"
    )
    await message.answer(text)

# Обработчик кнопки "Сменить часовой пояс" или команды /settimezone
@router.message(F.text.lower().in_({"сменить часовой пояс", "/settimezone"}))
async def change_utc(message: types.Message, state: FSMContext):
    await message.answer("Выберите ваш часовой пояс (смещение относительно UTC):",
                         reply_markup=utc_selection_keyboard())
    await state.set_state(ProfileStates.waiting_for_utc)

# Обработка inline-кнопок с выбором смещения
@router.callback_query(F.data.startswith("utc_"))
async def utc_chosen(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data
    if data == "utc_manual":
        await callback.message.answer("Введите смещение в часах (например, 5.5 для UTC+5:30):")
        await state.set_state(ProfileStates.waiting_for_utc)
        await callback.answer()
        return

    offset = float(data.split("_")[1])
    user_id = callback.from_user.id
    set_utc_offset(user_id, offset)
    await callback.message.answer(f"✅ Часовой пояс установлен: UTC{offset:+}")
    await state.clear()
    await callback.answer()

# Обработка ручного ввода (число)
@router.message(ProfileStates.waiting_for_utc)
async def manual_utc_entered(message: types.Message, state: FSMContext):
    try:
        offset = float(message.text.replace(",", "."))
        if not -12 <= offset <= 14:
            raise ValueError
        user_id = message.from_user.id
        set_utc_offset(user_id, offset)
        await message.answer(f"✅ Часовой пояс сохранён: UTC{offset:+.1f}")
        await state.clear()
    except ValueError:
        await message.answer("❌ Некорректно. Введите число от -12 до 14 (допустимы дробные, например 5.5). Попробуйте снова или нажмите /cancel")