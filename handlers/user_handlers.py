# handlers/user_handlers.py
from aiogram import Router, types
from aiogram import F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from database import Database
from keyboards import get_main_menu, get_edit_profile_keyboard, get_back_button_keyboard, \
    get_edit_counter_menu, get_edit_counters_menu, get_consent_keyboard, get_about_developer_keyboard, \
    get_phone_keyboard
from texts import Texts
from buttons import Buttons, InlineButtons

router = Router()
db = Database()

class Registration(StatesGroup):
    waiting_for_account_number = State()  # 1. Номер особового рахунку
    waiting_for_name = State()  # 2. ПІБ власника рахунку
    waiting_for_address = State()  # 3. Адреса
    waiting_for_phone = State()  # 4. Номер телефону
    waiting_for_meters_count = State()  # 5. Кількість лічильників
    personal_data_consent = State()  # Согласие на обработку данных
class SubmitReadings(StatesGroup):
    waiting_for_counter = State()
    waiting_for_reading = State()


class AddCounter(StatesGroup):
    waiting_for_alias = State()


class EditProfile(StatesGroup):
    waiting_for_field = State()
    waiting_for_new_value = State()
    waiting_for_new_full_name = State()
    waiting_for_new_address = State()
    waiting_for_new_account_number = State()
    waiting_for_new_count_of_meters = State()


class EditCounters(StatesGroup):
    waiting_for_counter_selection = State()
    waiting_for_counter_action = State()
    waiting_for_new_name = State()


@router.message(Command(commands=["start"]))
async def start(message: types.Message, state: FSMContext):
    print("Команда /start получена (user_handlers)")
    user_id = message.from_user.id
    user = db.get_user(user_id)

    print(user)

    if not user:
        await message.answer(Texts.START, reply_markup=ReplyKeyboardRemove())
        await message.answer("Введіть номер особового рахунку:")
        await state.set_state(Registration.waiting_for_account_number)
    else:
        await message.answer(Texts.WELLCOME, reply_markup=get_main_menu())


@router.message(Registration.waiting_for_account_number)
async def process_account_number(message: types.Message, state: FSMContext):
    # Проверяем что введено число
    if not message.text.isdigit():
        await message.answer("Номер особового рахунку повинен містити тільки цифри. Спробуйте ще раз.")
        return

    await state.update_data(account_number=message.text)
    await message.answer("Введіть ваше ПІБ:")
    await state.set_state(Registration.waiting_for_name)


@router.message(Registration.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    print(f"Получено ПІБ: {message.text}")
    await state.update_data(full_name=message.text)
    await message.answer(Texts.ADDRESS, reply_markup=ReplyKeyboardRemove())
    await state.set_state(Registration.waiting_for_address)


@router.message(Registration.waiting_for_address)
async def process_address(message: types.Message, state: FSMContext):
    print(f"Получен адрес: {message.text}")
    await state.update_data(address=message.text)

    await message.answer(
        "Тепер введіть номер телефону власника рахунку.\n\n"
        "Ви можете:\n"
        "• Ввести номер вручну (наприклад, +380123456789)\n"
        "• Натиснути кнопку 'Надіслати номер телефону,якщо Ви власник'",
        reply_markup=get_phone_keyboard()
    )
    await state.set_state(Registration.waiting_for_phone)


@router.message(Registration.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    # Обробка натискання кнопки "Назад"
    if message.text == Buttons.BACK:
        await message.answer(Texts.ADDRESS, reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(Registration.waiting_for_address)
        return

    # Отримання номера телефону
    if message.contact:
        # Номер з контакту
        phone = message.contact.phone_number
        # Додаємо '+' якщо його немає
        phone = phone if phone.startswith('+') else f'+{phone}'
    else:
        # Номер, введений вручну
        phone = message.text.replace(' ', '').replace('(', '').replace(')', '').replace('-', '')

    # Перевірка формату номера телефону
    if not (phone.startswith('+38') and len(phone) == 13 and phone[3:].isdigit()):
        await message.answer(
            "Будь ласка, введіть номер телефону у форматі +380XXXXXXXXX\n\n"
            "Або скористайтеся кнопкою 'Надіслати мій номер телефону'",
            reply_markup=get_phone_keyboard()
        )
        return

    print(f"Получено номер телефону: {phone}")
    await state.update_data(phone_number=phone)
    await message.answer(Texts.METERS_COUNT, reply_markup=ReplyKeyboardRemove())
    await state.set_state(Registration.waiting_for_meters_count)


@router.message(Registration.waiting_for_meters_count)
async def process_meters_count(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Будь ласка, введіть число.")
        return

    meters_count = int(message.text)

    # Проверяем ограничение
    if meters_count < 1 or meters_count > 3:
        await message.answer("Кількість лічильників повинна бути від 1 до 3.")
        return

    await state.update_data(water_meters_count=meters_count)

    await message.answer(
        "Для завершення реєстрації необхідно надати згоду на обробку ваших персональних даних.\n\n"
        "Ви даєте згоду на обробку наданих вами особистих даних?",
        reply_markup=get_consent_keyboard()
    )
    await state.set_state(Registration.personal_data_consent)




@router.message(Registration.personal_data_consent)
@router.message(Registration.personal_data_consent)
async def process_personal_data_consent(message: types.Message, state: FSMContext):
    if message.text == Buttons.CONSENT_YES:
        user_data = await state.get_data()
        db.add_user(
            user_id=message.from_user.id,
            full_name=user_data["full_name"],
            phone_number=user_data["phone_number"],
            address=user_data["address"],
            water_meters_count=user_data["water_meters_count"],
            account_number=user_data["account_number"]
        )

        user_id = message.from_user.id
        for i in range(1, user_data["water_meters_count"] + 1):
            db.add_counter(user_id, f"Лічильник-{i}")

        await message.answer(Texts.REGISTRATION_COMPLETE, reply_markup=get_main_menu())
        await state.clear()

    elif message.text == Buttons.CONSENT_NO:
        await message.answer(
            "На жаль, без згоди на обробку персональних даних ми не можемо завершити реєстрацію. "
            "Ви можете розпочати реєстрацію знову за командою /start.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await state.clear()
    else:
        await message.answer(
            "Будь ласка, оберіть 'Так, я даю згоду ✅' або 'Ні, я не даю згоду ❌'",
            reply_markup=get_consent_keyboard()
        )
@router.message(Command("add_counter"))
async def add_counter(message: types.Message, state: FSMContext):
    print("Команда /add_counter получена")
    await message.answer(Texts.COUNTER_ALIAS)
    await state.set_state(AddCounter.waiting_for_alias)

@router.message(AddCounter.waiting_for_alias)
async def process_alias(message: types.Message, state: FSMContext):
    print(f"Получен алиас счетчика: {message.text}")
    user_id = message.from_user.id
    alias = message.text

    db.cursor.execute("INSERT INTO counters (user_id, alias) VALUES (?, ?)", (user_id, alias))
    db.conn.commit()

    await message.answer(Texts.COUNTER_ADDED.format(alias=alias), reply_markup=get_main_menu())
    await state.clear()

@router.message(lambda message: message.text == Buttons.SUBMIT_READINGS)
async def start_submit_readings(message: types.Message, state: FSMContext):
    # Получаем список счетчиков пользователя
    user_id = message.from_user.id
    counters = db.get_counters(user_id)

    if not counters:
        await message.answer("У вас немає зареєстрованих лічильників.")
        return

    # Формируем клавиатуру с выбором счетчика
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            *[[KeyboardButton(text=counter[2])] for counter in counters],  # counter[2] — это alias
            [KeyboardButton(text=Buttons.BACK)]  # Добавляем кнопку "Назад"
        ],
        resize_keyboard=True
    )
    await message.answer("Оберіть лічильник:", reply_markup=keyboard)
    await state.set_state(SubmitReadings.waiting_for_counter)

@router.message(SubmitReadings.waiting_for_counter)
async def process_counter_selection(message: types.Message, state: FSMContext):
    if message.text == Buttons.BACK:
        await message.answer("Головне меню:", reply_markup=get_main_menu())
        await state.clear()
        return

    user_id = message.from_user.id
    counters = db.get_counters(user_id)
    selected_counter = next((counter for counter in counters if counter[2] == message.text), None)

    if not selected_counter:
        await message.answer("Лічильник не знайдено. Спробуйте ще раз.")
        return

    # Получаем последнее показание для выбранного счетчика
    last_reading = db.get_last_reading(selected_counter[0])

    # Сохраняем выбранный счетчик в состоянии
    await state.update_data(counter_id=selected_counter[0], counter_alias=selected_counter[2])
    await state.update_data(counter_id=selected_counter[0], counter_alias=selected_counter[2])
    await message.answer(
        f"Поточне значення лічильника '{selected_counter[2]}': {last_reading if last_reading else 'немає даних'}\n\n"
        f"Введіть нові показники:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(SubmitReadings.waiting_for_reading)


@router.message(SubmitReadings.waiting_for_reading)
async def process_reading(message: types.Message, state: FSMContext):
    # Проверяем, что введено число
    if not message.text.isdigit():
        await message.answer("Будь ласка, введіть число.")
        return

    # Получаем данные из состояния
    data = await state.get_data()
    counter_id = data["counter_id"]
    counter_alias = data["counter_alias"]
    reading_value = int(message.text)

    # Получаем последние показания для этого счетчика
    last_reading = db.get_last_reading(counter_id)

    # Проверяем, что новое показание больше предыдущего
    if last_reading is not None and reading_value <= last_reading:
        await message.answer(
            f"Помилка: нові показники ({reading_value}) повинні бути більшими за попередні ({last_reading}).",
            reply_markup=get_main_menu()
        )
        await state.clear()
        return

    try:
        # Сохраняем новые показания
        db.add_reading(counter_id, reading_value)

        # Формируем сообщение с результатами
        response = (
            f"✅ Показники для '{counter_alias}' успішно збережено!\n"
            f"Попередні показання: {last_reading if last_reading is not None else 'немає'}\n"
            f"Нові показання: {reading_value}\n"
            f"Різниця: {reading_value - last_reading if last_reading is not None else 'немає'}"
        )

        await message.answer(response, reply_markup=get_main_menu())
    except Exception as e:
        print(f"Error saving reading: {e}")
        await message.answer(
            "Сталася помилка при збереженні показників. Спробуйте ще раз.",
            reply_markup=get_main_menu()
        )
    finally:
        await state.clear()

@router.message(lambda message: message.text == Buttons.ADD_COUNTER)
async def start_add_counter(message: types.Message, state: FSMContext):
    print("Кнопка 'Додати лічильник' нажата")
    await message.answer(Texts.COUNTER_ALIAS)
    await state.set_state(AddCounter.waiting_for_alias)


@router.message(lambda message: message.text == Buttons.SUBMIT_READINGS)
async def start_submit_readings(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    counters = db.get_counters(user_id)

    if not counters:
        await message.answer("У вас немає зареєстрованих лічильників.")
        return

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for counter in counters:
        keyboard.add(KeyboardButton(text=counter[2]))  # counter[2] - это alias

    keyboard.add(KeyboardButton(text=Buttons.BACK))

    await message.answer("Оберіть лічильник:", reply_markup=keyboard)
    await state.set_state(SubmitReadings.waiting_for_counter)

@router.message(lambda message: message.text == Buttons.EDIT_PROFILE)
async def start_edit_profile(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user = db.get_user(user_id)

    if not user:
        await message.answer("Спочатку зареєструйтесь за допомогою команди /start.")
        return

    await message.answer("Оберіть поле для редагування:", reply_markup=get_edit_profile_keyboard())
    return

@router.message(lambda message: message.text == Buttons.FULL_NAME)
async def start_edit_full_name(message: types.Message, state: FSMContext):
    await message.answer("Введіть ПІБ валсника рахунку!\n\nНаприклад: Шевченко Тарас Григорович", reply_markup=get_back_button_keyboard())
    await state.set_state(EditProfile.waiting_for_new_full_name)
    return

@router.message(lambda message: message.text == Buttons.ADDRESS)
async def start_edit_address(message: types.Message, state: FSMContext):
    await message.answer("Введіть Нову адрессу валсника рахунку!\n\nНаприклад: вул. Центральна, 1, кв 1)", reply_markup=get_back_button_keyboard())
    await state.set_state(EditProfile.waiting_for_new_address)
    return

@router.message(lambda message: message.text == Buttons.ACCOUNT_NUMBER)
async def start_edit_account_number(message: types.Message, state: FSMContext):
    await message.answer("Введіть Новий номер особистого рахунку!", reply_markup=get_back_button_keyboard())
    await state.set_state(EditProfile.waiting_for_new_account_number)
    return



@router.message(EditProfile.waiting_for_field)
async def process_field_selection(message: types.Message, state: FSMContext):
    field = message.text

    valid_fields = [
        Buttons.FULL_NAME,
        Buttons.ADDRESS,
        Buttons.COUNT_OF_METERS,
        Buttons.ACCOUNT_NUMBER
    ]

    if field not in valid_fields:
        await message.answer("Будь ласка, оберіть поле зі списку.")
        return

    user_id = message.from_user.id
    user = db.get_user(user_id)

    # Получаем текущее значение выбранного поля
    if field == Buttons.FULL_NAME:
        current_value = user[2]  # full_name
    elif field == Buttons.ADDRESS:
        current_value = user[4]  # address
    elif field == Buttons.COUNT_OF_METERS:
        current_value = user[5]  # water_meters_count
    elif field == Buttons.ACCOUNT_NUMBER:
        current_value = user[6]  # account_number

    await state.update_data(field=field)
    await message.answer(
        f"Поточне значення поля '{field}': {current_value}\n\nВведіть нове значення або натисніть 'Назад':",
        reply_markup=get_back_button_keyboard()
    )
    await state.set_state(EditProfile.waiting_for_new_value)

@router.message(EditProfile.waiting_for_new_value)
async def process_new_value(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        # Возвращаемся к выбору поля для редактирования
        await message.answer("Оберіть поле для редагування:", reply_markup=get_edit_profile_keyboard())
        await state.set_state(EditProfile.waiting_for_field)
        return

    user_id = message.from_user.id
    data = await state.get_data()
    field = data["field"]
    new_value = message.text

    # Обновляем данные в базе данных
    if field == Buttons.FULL_NAME:
        db.cursor.execute("UPDATE users SET full_name = ? WHERE user_id = ?", (new_value, user_id))
    elif field == Buttons.ADDRESS:
        db.cursor.execute("UPDATE users SET address = ? WHERE user_id = ?", (new_value, user_id))
    elif field == Buttons.COUNT_OF_METERS:
        if not new_value.isdigit():
            await message.answer("Кількість лічильників повинна бути числом.")
            return
        db.cursor.execute("UPDATE users SET water_meters_count = ? WHERE user_id = ?", (int(new_value), user_id))
    elif field == Buttons.ACCOUNT_NUMBER:
        db.cursor.execute("UPDATE users SET account_number = ? WHERE user_id = ?", (new_value, user_id))

    db.conn.commit()
    await message.answer(f"Поле '{field}' успішно оновлено!", reply_markup=get_main_menu())
    await state.clear()

# edit full name
#     waiting_for_new_count_of_meters = State()
#     waiting_for_new_account_number = State()
@router.message(EditProfile.waiting_for_new_full_name)
async def process_edit_new_full_name(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    new_full_name = message.text

    db.cursor.execute("UPDATE users SET full_name = ? WHERE user_id = ?", (new_full_name, user_id))
    db.conn.commit()

    await message.answer(f"'ПІБ' успішно оновлено!", reply_markup=get_main_menu())
    await state.clear()

    return

@router.message(EditProfile.waiting_for_new_address)
async def process_edit_new_address(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    new_address = message.text

    db.cursor.execute("UPDATE users SET address = ? WHERE user_id = ?", (new_address, user_id))
    db.conn.commit()

    await message.answer(f"Адреса успішно оновлена!", reply_markup=get_main_menu())
    await state.clear()

    return


@router.message(EditProfile.waiting_for_new_account_number)
async def process_edit_new_account_number(message: types.Message, state: FSMContext):
    # Проверяем что введено число
    if not message.text.isdigit():
        await message.answer("Номер особового рахунку повинен містити тільки цифри. Спробуйте ще раз.")
        return

    user_id = message.from_user.id
    db.cursor.execute(
        "UPDATE users SET account_number = ? WHERE user_id = ?",
        (message.text, user_id)
    )
    db.conn.commit()

    await message.answer(f"Номер особистого рахунку успішно оновлений!", reply_markup=get_main_menu())
    await state.clear()


@router.message(lambda message: message.text == Buttons.EDIT_COUNTERS)
async def start_edit_counters(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    counters = db.get_counters(user_id)

    if not counters:
        await message.answer("У вас немає зареєстрованих лічильників.", reply_markup=get_main_menu())
        return

    # Формируем клавиатуру с выбором счетчика
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=counter[2])] for counter in counters],  # counter[2] — это alias
        resize_keyboard=True
    )
    keyboard.keyboard.append([KeyboardButton(text=Buttons.BACK)])  # Добавляем кнопку "Назад"

    await message.answer("Оберіть лічильник для редагування:", reply_markup=keyboard)
    await state.set_state(EditCounters.waiting_for_counter_selection)

@router.message(EditCounters.waiting_for_counter_selection)
async def process_counter_selection(message: types.Message, state: FSMContext):
    if message.text == Buttons.BACK:
        await message.answer("Головне меню:", reply_markup=get_main_menu())
        await state.clear()
        return

    user_id = message.from_user.id
    counters = db.get_counters(user_id)
    selected_counter = next((counter for counter in counters if counter[2] == message.text), None)

    if not selected_counter:
        await message.answer("Лічильник не знайдено. Спробуйте ще раз.")
        return

    await state.update_data(counter_id=selected_counter[0], counter_alias=selected_counter[2])
    await message.answer(f"Оберіть дію для лічильника '{selected_counter[2]}':", reply_markup=get_edit_counter_menu())
    await state.set_state(EditCounters.waiting_for_counter_action)

@router.message(EditCounters.waiting_for_counter_action)
async def process_counter_action(message: types.Message, state: FSMContext):
    if message.text == Buttons.BACK:
        await message.answer("Оберіть лічильник для редагування:", reply_markup=get_edit_counters_menu())
        await state.set_state(EditCounters.waiting_for_counter_selection)
        return

    data = await state.get_data()
    counter_id = data["counter_id"]
    counter_alias = data["counter_alias"]

    if message.text == Buttons.EDIT_COUNTER_NAME:
        await message.answer(f"Введіть нову назву для лічильника '{counter_alias}':", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(EditCounters.waiting_for_new_name)
    elif message.text == Buttons.DELETE_COUNTER:
        db.cursor.execute("DELETE FROM counters WHERE id = ?", (counter_id,))
        db.conn.commit()
        await message.answer(f"Лічильник '{counter_alias}' успішно видалено!", reply_markup=get_main_menu())
        await state.clear()

@router.message(EditCounters.waiting_for_new_name)
async def process_new_name(message: types.Message, state: FSMContext):
    new_name = message.text
    data = await state.get_data()
    counter_id = data["counter_id"]

    db.cursor.execute("UPDATE counters SET alias = ? WHERE id = ?", (new_name, counter_id))
    db.conn.commit()
    await message.answer(f"Назву лічильника успішно оновлено на '{new_name}'!", reply_markup=get_main_menu())
    await state.clear()

@router.message(lambda message: message.text == Buttons.ABOUT)
async def show_about_us(message: types.Message):
    # Створюємо інлайн-клавіатуру з кнопкою про розробника
    await message.answer(Texts.ABOUT_US, reply_markup=get_main_menu())

    # Додаємо інлайн-клавіатуру до попереднього повідомлення
    await message.answer(
        "Хочете дізнатися про розробника?",
        reply_markup=get_about_developer_keyboard()
    )

@router.callback_query(lambda c: c.data == "show_developer_info")
async def show_developer_info(callback: types.CallbackQuery):

    # Видаляємо попередню інлайн-клавіатуру
    await callback.message.edit_reply_markup(reply_markup=None)

    # Надсилаємо інформацію про розробника
    await callback.message.answer(Texts.ABOUT_DEVELOPER)

    # Обов'язково треба відповісти на callback_query
    await callback.answer()

@router.message(Registration.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    # Обробка натискання кнопки "Назад"
    if message.text == Buttons.BACK:
        await message.answer(Texts.NAME, reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(Registration.waiting_for_name)
        return

    # Отримання номера телефону
    if message.contact:
        # Номер з контакту
        phone = message.contact.phone_number
        # Додаємо '+' якщо його немає
        phone = phone if phone.startswith('+') else f'+{phone}'
    else:
        # Номер, введений вручну
        phone = message.text.replace(' ', '').replace('(', '').replace(')', '').replace('-', '')

    # Перевірка формату номера телефону
    if not (phone.startswith('+38') and len(phone) == 13 and phone[3:].isdigit()):
        await message.answer(
            "Будь ласка, введіть номер телефону у форматі +380XXXXXXXXX\n\n"
            "Або скористайтеся кнопкою 'Надіслати мій номер телефону'",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    print(f"Получено номер телефону: {phone}")
    await state.update_data(phone_number=phone)

    await message.answer(Texts.ADDRESS, reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(Registration.waiting_for_address)
@router.message(lambda message: message.text == Buttons.COUNT_OF_METERS)
async def start_edit_count_of_meters(message: types.Message, state: FSMContext):
    await message.answer("Введіть нову кількість лічильників:", reply_markup=get_back_button_keyboard())
    await state.set_state(EditProfile.waiting_for_new_count_of_meters)


@router.message(EditProfile.waiting_for_new_count_of_meters)
async def process_edit_count_of_meters(message: types.Message, state: FSMContext):
    if message.text == Buttons.BACK:
        await message.answer("Оберіть поле для редагування:", reply_markup=get_edit_profile_keyboard())
        await state.set_state(EditProfile.waiting_for_field)
        return

    if not message.text.isdigit():
        await message.answer("Будь ласка, введіть число.")
        return

    new_count = int(message.text)

    # Проверяем ограничение
    if new_count < 1 or new_count > 3:
        await message.answer("Кількість лічильників повинна бути від 1 до 3.")
        return

    user_id = message.from_user.id
    current_count = db.get_user(user_id)[5]  # Получаем текущее количество счетчиков

    # Обновляем количество счетчиков в базе данных
    db.cursor.execute("UPDATE users SET water_meters_count = ? WHERE user_id = ?", (new_count, user_id))

    if new_count > current_count:
        # Добавляем новые счетчики
        for i in range(current_count + 1, new_count + 1):
            db.add_counter(user_id, f"Лічильник-{i}")
    elif new_count < current_count:
        # Удаляем лишние счетчики (начиная с последнего)
        counters = db.get_counters(user_id)
        for counter in counters[new_count:]:
            db.cursor.execute("DELETE FROM counters WHERE id = ?", (counter[0],))

    db.conn.commit()
    await message.answer(f"Кількість лічильників успішно оновлено на {new_count}!", reply_markup=get_main_menu())
    await state.clear()
@router.message(lambda message: message.text == Buttons.GO_HOME)
async def go_to_main_menu(message: types.Message, state: FSMContext):
    await message.answer("Головна:", reply_markup=get_main_menu())
    await state.clear()
