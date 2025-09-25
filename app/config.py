import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
# Храни дату/время в одном стиле: либо локально, либо UTC.
# Для простоты оставим локальное время системы.
DEFAULT_TZ = os.getenv("BOT_TZ", "local")  # для будущих доработок
