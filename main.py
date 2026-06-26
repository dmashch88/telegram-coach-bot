import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from contextlib import asynccontextmanager

from config import BOT_TOKEN
from database import init_db
from scheduler import setup_scheduler, scheduler
from handlers import start, morning, evening, common

logging.basicConfig(level=logging.INFO)

async def main():
    init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Подключаем роутеры
    dp.include_router(start.router)
    dp.include_router(morning.router)
    dp.include_router(evening.router)
    dp.include_router(common.router)

    # Настраиваем планировщик
    setup_scheduler(bot)

    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)

if __name__ == "__main__":
    asyncio.run(main())
