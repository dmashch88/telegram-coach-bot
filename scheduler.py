from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, date
import asyncio
from aiogram import Bot
import json
import random
import pytz

from config import MORNING_TIME, EVENING_TIME, TIMEZONE
from database import get_all_users_with_goal, get_daily_status, update_daily_status, get_user
from handlers.morning import send_morning_message
from handlers.evening import send_evening_message

scheduler = AsyncIOScheduler()

def load_quotes():
    with open("data/quotes.txt", "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def load_phrases():
    with open("data/phrases.json", "r", encoding="utf-8") as f:
        return json.load(f)

QUOTES = load_quotes()
PHRASES = load_phrases()

async def morning_task(bot: Bot):
    today = date.today().isoformat()
    users = get_all_users_with_goal()
    for user in users:
        status = get_daily_status(user['id'])
        if status.get('last_morning') == today:
            continue
        try:
            await send_morning_message(bot, user['telegram_id'], user['goal_text'])
            update_daily_status(user['id'], "morning", today)
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Morning error for {user['telegram_id']}: {e}")

async def evening_task(bot: Bot):
    today = date.today().isoformat()
    users = get_all_users_with_goal()
    for user in users:
        status = get_daily_status(user['id'])
        if status.get('last_evening') == today:
            continue
        try:
            await send_evening_message(bot, user['telegram_id'], user['goal_text'])
            update_daily_status(user['id'], "evening", today)
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Evening error for {user['telegram_id']}: {e}")

def setup_scheduler(bot: Bot):
    tz = pytz.timezone(TIMEZONE)
    hour_m, minute_m = map(int, MORNING_TIME.split(':'))
    scheduler.add_job(
        morning_task,
        trigger=CronTrigger(hour=hour_m, minute=minute_m, timezone=tz),
        args=[bot],
        id="morning_job"
    )
    hour_e, minute_e = map(int, EVENING_TIME.split(':'))
    scheduler.add_job(
        evening_task,
        trigger=CronTrigger(hour=hour_e, minute=minute_e, timezone=tz),
        args=[bot],
        id="evening_job"
    )
    scheduler.start()
