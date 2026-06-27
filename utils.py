import re
from datetime import datetime
import pytz
from config import MORNING_START, MORNING_END, EVENING_START, EVENING_END

def validate_timezone(tz_str: str) -> bool:
    try:
        pytz.timezone(tz_str)
        return True
    except pytz.UnknownTimeZoneError:
        return False

def get_user_timezone_str(utc_offset: str) -> str:
    """
    Преобразует строку вида '+3' или '-5' в часовой пояс типа 'Etc/GMT-3'.
    """
    match = re.match(r"^([+-])(\d{1,2})$", utc_offset.strip())
    if not match:
        return None
    sign, hours = match.groups()
    offset_hours = int(hours)
    if sign == '-':
        offset_hours = -offset_hours
    # В Etc/GMT знак инвертирован: Etc/GMT-3 означает +3
    return f"Etc/GMT{'+' if offset_hours < 0 else '-'}{abs(offset_hours)}"

def get_current_time_in_tz(tz_str: str) -> datetime:
    tz = pytz.timezone(tz_str)
    return datetime.now(tz)

def is_within_window(tz_str: str, window_type: str) -> bool:
    now = get_current_time_in_tz(tz_str)
    hour = now.hour
    if window_type == "morning":
        return MORNING_START <= hour < MORNING_END
    elif window_type == "evening":
        return EVENING_START <= hour < EVENING_END
    return False

def get_next_window_info(tz_str: str):
    now = get_current_time_in_tz(tz_str)
    hour = now.hour
    if hour < MORNING_START:
        return "morning", MORNING_START - hour
    elif hour < MORNING_END:
        return "morning", 0
    elif hour < EVENING_START:
        return "evening", EVENING_START - hour
    elif hour < EVENING_END:
        return "evening", 0
    else:
        return "morning", (24 - hour) + MORNING_START

def get_today_str(tz_str: str) -> str:
    return get_current_time_in_tz(tz_str).strftime("%Y-%m-%d")