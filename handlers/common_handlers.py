# handlers/common_handlers.py
from aiogram import Router, types
from aiogram.filters import Command
from aiogram import Dispatcher

router = Router()

def register_handlers(dp: Dispatcher):
    dp.include_router(router)