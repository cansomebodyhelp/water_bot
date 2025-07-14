from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from buttons import Buttons, InlineButtons, AdminButtons


def get_start_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=Buttons.START_BOT)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard

def get_main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=Buttons.SUBMIT_READINGS)],
            [KeyboardButton(text=Buttons.EDIT_PROFILE)],
            [KeyboardButton(text=Buttons.ABOUT)],
        ],
        resize_keyboard=True
    )
    return keyboard

def get_edit_counters_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=Buttons.ADD_COUNTER)],
            [KeyboardButton(text=Buttons.EDIT_COUNTER)],
            [KeyboardButton(text=Buttons.BACK)]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_edit_counter_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=Buttons.EDIT_COUNTER_NAME)],
            [KeyboardButton(text=Buttons.DELETE_COUNTER)],
            [KeyboardButton(text=Buttons.BACK)]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_edit_profile_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=Buttons.FULL_NAME)],
            [KeyboardButton(text=Buttons.ADDRESS)],
            [KeyboardButton(text=Buttons.COUNT_OF_METERS)],
            [KeyboardButton(text=Buttons.ACCOUNT_NUMBER)],
            [KeyboardButton(text=Buttons.GO_HOME)]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_back_button_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=Buttons.BACK)]],
        resize_keyboard=True
    )
    return keyboard

def get_consent_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=Buttons.CONSENT_YES),
                KeyboardButton(text=Buttons.CONSENT_NO)
            ]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_about_developer_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=InlineButtons.ABOUT_DEVELOPER,
            callback_data="show_developer_info"
        )]
    ])
    return keyboard

def get_phone_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(
                text=Buttons.SHARE_PHONE,
                request_contact=True
            )]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard

def get_admin_login_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=AdminButtons.LOGIN)]],
        resize_keyboard=True
    )

def get_admin_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=AdminButtons.READINGS_REPORT)]],
        resize_keyboard=True
    )

def get_date_range_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=AdminButtons.CURRENT_MONTH),
                # KeyboardButton(text=AdminButtons.PREV_MONTH)
            ],
            # [KeyboardButton(text=AdminButtons.CUSTOM_PERIOD)]
            [KeyboardButton(text=AdminButtons.BACK)]
        ],
        resize_keyboard=True
    )
def get_date_range_selection_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=AdminButtons.SELECT_DATE_RANGE)],
            [KeyboardButton(text=AdminButtons.BACK)]
        ],
        resize_keyboard=True,
        input_field_placeholder="Оберіть дію..."
    )
def get_confirmation_keyboard(yes_text="Так", no_text="Ні"):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=yes_text)],
            [KeyboardButton(text=no_text)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )