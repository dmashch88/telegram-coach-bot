from datetime import datetime, timedelta

def get_local_time(utc_offset, utc_time=None):
    """Возвращает текущее локальное время пользователя по UTC+offset"""
    if utc_time is None:
        utc_time = datetime.utcnow()
    return utc_time + timedelta(hours=utc_offset)

def local_to_utc(local_dt, utc_offset):
    """Преобразует локальное datetime в UTC для хранения"""
    return local_dt - timedelta(hours=utc_offset)

def format_time(dt, fmt="%d.%m.%Y %H:%M"):
    return dt.strftime(fmt)