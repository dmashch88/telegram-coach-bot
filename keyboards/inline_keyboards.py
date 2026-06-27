from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def utc_selection_keyboard():
    offsets = list(range(-12, 13))
    buttons = []
    row = []
    for i, off in enumerate(offsets):
        label = f"UTC{off:+d}" if off != 0 else "UTC±0"
        row.append(InlineKeyboardButton(text=label, callback_data=f"utc_{off}"))
        if (i + 1) % 6 == 0 or i == len(offsets) - 1:
            buttons.append(row)
            row = []
    buttons.append([InlineKeyboardButton(text="Ввести вручную", callback_data="utc_manual")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Остальные клавиатуры из оригинального файла (главное меню, календарь и т.д.)
# должны быть ниже. Приведён только новый фрагмент; сохраните остальные.