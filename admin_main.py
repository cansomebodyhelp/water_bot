import asyncio
import os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, FSInputFile
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import Database
from config import ADMIN_TOKEN, ADMIN_PASSWORD, DATABASE_NAME
import traceback

# Список авторизованных админов
authorized_admins = set()

db = Database(DATABASE_NAME)

class AdminStates(StatesGroup):
    waiting_for_password = State()
    waiting_for_start_date = State()
    waiting_for_end_date = State()

router = Router()

# Украинские названия месяцев
MONTHS_UA = {
    1: "Січень", 2: "Лютий", 3: "Березень", 4: "Квітень",
    5: "Травень", 6: "Червень", 7: "Липень", 8: "Серпень",
    9: "Вересень", 10: "Жовтень", 11: "Листопад", 12: "Грудень"
}

def get_admin_menu():
    """Создает главное меню админа"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Сформувати звіт за період")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_back_keyboard():
    """Создает клавиатуру с кнопкой 'Назад'"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )
    return keyboard

def create_calendar_keyboard(year: int, month: int):
    """Создает инлайн-клавиатуру календаря"""
    builder = InlineKeyboardBuilder()

    # Заголовок с месяцем и годом
    builder.row(
        InlineKeyboardButton(
            text=f"{MONTHS_UA[month]} {year}",
            callback_data="ignore"
        )
    )

    # Кнопки навигации по месяцам
    builder.row(
        InlineKeyboardButton(text="⬅️", callback_data=f"prev_month_{year}_{month}"),
        InlineKeyboardButton(text="➡️", callback_data=f"next_month_{year}_{month}")
    )

    # Дни недели
    builder.row(
        InlineKeyboardButton(text="Пн", callback_data="ignore"),
        InlineKeyboardButton(text="Вт", callback_data="ignore"),
        InlineKeyboardButton(text="Ср", callback_data="ignore"),
        InlineKeyboardButton(text="Чт", callback_data="ignore"),
        InlineKeyboardButton(text="Пт", callback_data="ignore"),
        InlineKeyboardButton(text="Сб", callback_data="ignore"),
        InlineKeyboardButton(text="Нд", callback_data="ignore")
    )

    # Получаем первый день месяца и количество дней
    first_day = datetime(year, month, 1)
    start_weekday = first_day.weekday()

    # Количество дней в месяце
    if month == 12:
        days_in_month = (datetime(year + 1, 1, 1) - first_day).days
    else:
        days_in_month = (datetime(year, month + 1, 1) - first_day).days

    # Создаем кнопки для дней
    days_buttons = []

    # Пустые кнопки для дней предыдущего месяца
    for _ in range(start_weekday):
        days_buttons.append(InlineKeyboardButton(text=" ", callback_data="ignore"))

    # Кнопки для дней текущего месяца
    for day in range(1, days_in_month + 1):
        days_buttons.append(
            InlineKeyboardButton(
                text=str(day),
                callback_data=f"select_date_{year}_{month}_{day}"
            )
        )

    # Группируем кнопки по 7 (неделя)
    for i in range(0, len(days_buttons), 7):
        week_buttons = days_buttons[i:i + 7]
        while len(week_buttons) < 7:
            week_buttons.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
        builder.row(*week_buttons)

    return builder.as_markup()

@router.message(Command("start"))
async def start_admin(message: types.Message, state: FSMContext):
    """Обработка команды /start для админа"""
    user_id = message.from_user.id

    if user_id in authorized_admins:
        await message.answer(
            "🔐 Ви вже авторизовані як адміністратор.\n\n"
            "Оберіть дію:",
            reply_markup=get_admin_menu()
        )
    else:
        await message.answer(
            "🔐 Для доступу до адмін-панелі введіть пароль:",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(AdminStates.waiting_for_password)

@router.message(AdminStates.waiting_for_password)
async def check_password(message: types.Message, state: FSMContext):
    """Проверка пароля"""
    if message.text == ADMIN_PASSWORD:
        user_id = message.from_user.id
        authorized_admins.add(user_id)

        await message.answer(
            "✅ Пароль вірний! Ласкаво просимо до адмін-панелі.\n\n"
            "Оберіть дію:",
            reply_markup=get_admin_menu()
        )
        await state.clear()
    else:
        await message.answer(
            "❌ Невірний пароль. Спробуйте ще раз:",
            reply_markup=ReplyKeyboardRemove()
        )

@router.message(F.text == "📊 Сформувати звіт за період")
async def start_report_generation(message: types.Message, state: FSMContext):
    """Начало формирования отчета"""
    user_id = message.from_user.id

    if user_id not in authorized_admins:
        await message.answer("❌ Ви не авторизовані. Введіть команду /start")
        return

    now = datetime.now()
    calendar_kb = create_calendar_keyboard(now.year, now.month)

    await message.answer(
        "📅 Оберіть початкову дату звіту:",
        reply_markup=get_back_keyboard()
    )

    await message.answer(
        "Оберіть день:",
        reply_markup=calendar_kb
    )

    await state.set_state(AdminStates.waiting_for_start_date)

@router.callback_query(F.data.startswith("prev_month_"))
async def prev_month(callback: types.CallbackQuery):
    """Переход к предыдущему месяцу"""
    _, _, year, month = callback.data.split("_")
    year, month = int(year), int(month)

    if month == 1:
        year -= 1
        month = 12
    else:
        month -= 1

    calendar_kb = create_calendar_keyboard(year, month)
    await callback.message.edit_reply_markup(reply_markup=calendar_kb)
    await callback.answer()

@router.callback_query(F.data.startswith("next_month_"))
async def next_month(callback: types.CallbackQuery):
    """Переход к следующему месяцу"""
    _, _, year, month = callback.data.split("_")
    year, month = int(year), int(month)

    if month == 12:
        year += 1
        month = 1
    else:
        month += 1

    calendar_kb = create_calendar_keyboard(year, month)
    await callback.message.edit_reply_markup(reply_markup=calendar_kb)
    await callback.answer()

@router.callback_query(F.data.startswith("select_date_"))
async def select_date(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора даты"""
    _, _, year, month, day = callback.data.split("_")
    selected_date = f"{day.zfill(2)}.{month.zfill(2)}.{year}"

    current_state = await state.get_state()

    if current_state == AdminStates.waiting_for_start_date:
        await state.update_data(start_date=selected_date)
        await callback.message.edit_text(f"✅ Початкова дата: {selected_date}")

        now = datetime.now()
        calendar_kb = create_calendar_keyboard(now.year, now.month)

        await callback.message.answer(
            "📅 Тепер оберіть кінцеву дату звіту:",
            reply_markup=calendar_kb
        )

        await state.set_state(AdminStates.waiting_for_end_date)

    elif current_state == AdminStates.waiting_for_end_date:
        await state.update_data(end_date=selected_date)
        await callback.message.edit_text(f"✅ Кінцева дата: {selected_date}")

        data = await state.get_data()
        start_date = data.get("start_date")
        end_date = selected_date

        await generate_report(callback.message, start_date, end_date, state)

    await callback.answer()

@router.callback_query(F.data == "ignore")
async def ignore_callback(callback: types.CallbackQuery):
    """Игнорирование нажатий на неактивные кнопки календаря"""
    await callback.answer()

async def generate_report(message: types.Message, start_date: str, end_date: str, state: FSMContext):
    """Генерация отчета за указанный период"""
    try:
        await message.answer("⏳ Формую звіт, будь ласка, зачекайте...")

        # Получаем данные из базы
        report_data = db.get_readings_report(start_date, end_date)

        if not report_data:
            await message.answer(
                "📋 За вказаний період дані відсутні.",
                reply_markup=get_admin_menu()
            )
            await state.clear()
            return

        # Генерируем Excel файл
        filename = db.export_to_excel(report_data)

        try:
            # Отправляем файл пользователю
            file = FSInputFile(filename)
            await message.answer_document(
                file,
                caption=f"📊 Звіт за період з {start_date} по {end_date}\n"
                        f"Кількість записів: {len(report_data)}"
            )
            print(f"[SUCCESS] Отчет {filename} успешно отправлен в Telegram")
        finally:
            # Удаляем временный файл после отправки или в случае ошибки
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                    print(f"[SUCCESS] Файл {filename} успешно удален с сервера")
                except Exception as e:
                    print(f"[ERROR] Ошибка при удалении файла {filename}: {str(e)}")

        await message.answer(
            "✅ Звіт успішно сформовано!",
            reply_markup=get_admin_menu()
        )

    except Exception as e:
        print(f"[ERROR] Помилка при генерації звіту: {str(e)}")
        traceback.print_exc()
        await message.answer(
            "❌ Сталася помилка при формуванні звіту. Спробуйте ще раз.",
            reply_markup=get_admin_menu()
        )
    finally:
        await state.clear()

@router.message(F.text == "🔙 Назад")
async def back_to_menu(message: types.Message, state: FSMContext):
    """Возврат в главное меню"""
    await message.answer(
        "🏠 Головне меню:",
        reply_markup=get_admin_menu()
    )
    await state.clear()

@router.message()
async def handle_unauthorized(message: types.Message):
    """Обработка сообщений от неавторизованных пользователей"""
    user_id = message.from_user.id

    if user_id not in authorized_admins:
        await message.answer(
            "❌ Ви не авторизовані. Введіть команду /start для авторизації."
        )
    else:
        await message.answer(
            "👤 Команда не розпізнана. Оберіть дію з меню:",
            reply_markup=get_admin_menu()
        )

async def main():
    """Главная функция запуска бота"""
    bot = Bot(token=ADMIN_TOKEN)
    dp = Dispatcher()

    dp.include_router(router)

    print("🤖 Адмін-бот запущено!")
    print(f"🔐 Пароль для доступу: {ADMIN_PASSWORD}")

    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"Помилка: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Адмін-бот вимкнено!")