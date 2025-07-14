import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from handlers.user_handlers import router as user_router
from config import BOT_TOKEN, DATABASE_NAME
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from database import Database
from utils.reminders import send_reminders

db = Database(DATABASE_NAME)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Регистрируем роутеры
    dp.include_router(user_router)

    # Инициализируем планировщик
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        send_reminders,
        "interval",
        days=1,  # Проверяем каждый день
        args=(bot,),
        next_run_time=datetime.now() + timedelta(seconds=10)  # Первое напоминание через 10 секунд
    )
    scheduler.start()

    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот ВИМКНЕНО")