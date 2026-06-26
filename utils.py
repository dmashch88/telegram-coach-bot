from datetime import datetime, timedelta
import pytz
from typing import Optional, Tuple

POPULAR_TIMEZONES = [
    "Europe/Moscow", "Europe/Kiev", "Europe/Minsk",
    "Asia/Almaty", "Asia/Tashkent", "Asia/Yekaterinburg",
    "Europe/Berlin", "Europe/Paris", "Europe/London",
    "America/New_York", "America/Chicago", "America/Los_Angeles",
    "Asia/Tokyo", "Asia/Shanghai", "Asia/Kolkata"
]

def validate_timezone(tz_name: str) -> bool:
    """Проверяет, существует ли такой часовой пояс."""
    return tz_name in pytz.all_timezones

def get_local_time(tz_name: str) -> Optional[datetime]:
    """Возвращает текущее время в указанном часовом поясе."""
    try:
        tz = pytz.timezone(tz_name)
        return datetime.now(tz)
    except Exception:
        return None

def is_within_window(tz_name: str, window_type: str) -> bool:
    """
    Проверяет, попадает ли текущее время в заданное окно.
    window_type: 'morning' (06:00-09:00) или 'evening' (21:00-23:59)
    """
    now = get_local_time(tz_name)
    if not now:
        return True
    hour = now.hour
    if window_type == "morning":
        return 6 <= hour < 9
    elif window_type == "evening":
        return hour >= 21
    return False

def get_next_window_info(tz_name: str) -> Optional[Tuple[str, str]]:
    """
    Возвращает ближайшее окно ('morning' или 'evening') и строку с временем до него.
    Если сейчас утро – вернёт вечер, и наоборот.
    """
    now = get_local_time(tz_name)
    if not now:
        return None
    tz = pytz.timezone(tz_name)
    current_hour = now.hour
    if 6 <= current_hour < 9:
        # Сейчас утро, следующее окно – вечер сегодня в 21:00
        target = now.replace(hour=21, minute=0, second=0, microsecond=0)
        delta = target - now
        hours, remainder = divmod(delta.seconds, 3600)
        minutes = remainder // 60
        return ("evening", f"{hours} ч {minutes} мин")
    elif current_hour >= 21:
        # Вечер, следующее окно – завтра утро в 6:00
        target = now.replace(hour=6, minute=0, second=0, microsecond=0) + timedelta(days=1)
        delta = target - now
        hours, remainder = divmod(delta.seconds, 3600)
        minutes = remainder // 60
        return ("morning", f"{hours} ч {minutes} мин")
    else:
        # Днём (9-21) – ближайшее окно вечер
        target = now.replace(hour=21, minute=0, second=0, microsecond=0)
        delta = target - now
        hours, remainder = divmod(delta.seconds, 3600)
        minutes = remainder // 60
        return ("evening", f"{hours} ч {minutes} мин")