import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
DATABASE_NAME = os.getenv("DATABASE_NAME")