import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from handlers.user_handlers import router as user_router
from handlers.admin_handlers import router as admin_router  # Предполагается, что admin_main.py перенесён в admin_handlers.py
from config import BOT_TOKEN, ADMIN_TOKEN, DATABASE_NAME
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from database import Database
from utils.reminders import send_reminders
from aiohttp import web

db = Database(DATABASE_NAME)

# HTTP-эндпоинт для health check
async def health_check(request):
    print(f"[HEALTH CHECK] Received request at {datetime.now()}")
    return web.Response(text="OK")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/health', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)  # Render использует порт 8080
    await site.start()
    print("HTTP-сервер запущен на порту 8080")

async def main():
    # Инициализация обоих ботов
    user_bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
    admin_bot = Bot(token=ADMIN_TOKEN)
    dp = Dispatcher()

    # Регистрируем роутеры
    dp.include_router(user_router)
    dp.include_router(admin_router)

    # Инициализируем планировщик
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        send_reminders,
        "interval",
        days=1,
        args=(user_bot,),
        next_run_time=datetime.now() + timedelta(seconds=10)
    )
    scheduler.start()

    # Запускаем веб-сервер
    asyncio.create_task(start_web_server())

    print("Бот запущен!")
    # Запускаем оба бота в одном Dispatcher
    await dp.start_polling(user_bot, admin_bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот ВИМКНЕНО")
