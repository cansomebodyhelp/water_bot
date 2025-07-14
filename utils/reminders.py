from datetime import datetime, timedelta

from aiogram import Bot

from database import Database

db = Database()

async def send_reminders(bot: Bot):
    today = datetime.now()
    # Рассчитываем последний день текущего месяца
    if today.month == 12:
        last_day_of_month = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_day_of_month = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

    # Рассчитываем разницу в днях до конца месяца
    days_until_end = (last_day_of_month - today).days

    # Отправляем напоминание, если до конца месяца осталось 5 дней
    if days_until_end == 5:
        users = db.get_all_users()
        for user in users:
            user_id = user[1]  # user_id находится на второй позиции в кортеже
            await bot.send_message(user_id, "Нагадування: залишилось 5 днів до кінця місяця. Будь ласка, передайте показники лічильників.")
