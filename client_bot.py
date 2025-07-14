import asyncio
from aiogram import Bot, Dispatcher
from handlers.admin_handlers import router as admin_router
from config import BOT_TOKEN
from database import Database

db = Database()

async def main():
    bot = Bot(token='7541308144:AAF3jI8mY0oYFATM8FfWX6OKNZ8JnVDwa_o')
    dp = Dispatcher()

    # Регистрируем роутеры
    dp.include_router(admin_router)

    print("Admin Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот ВИМКНЕНО")