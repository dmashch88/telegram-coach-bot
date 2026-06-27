import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from database import init_db
from handlers import start, morning, evening, common, off_window, stats, help
from scheduler import setup_scheduler

logging.basicConfig(level=logging.INFO)

async def main():
    # Инициализация БД
    init_db()
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Подключаем роутеры
    dp.include_router(start.router)
    dp.include_router(morning.router)
    dp.include_router(evening.router)
    dp.include_router(common.router)
    dp.include_router(off_window.router)  # должен быть последним (catch-all)
    dp.include_router(stats.router)
    dp.include_router(help.router)
    
    # Запускаем планировщик для напоминаний
    setup_scheduler(bot)
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())