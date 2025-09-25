import asyncio
from aiogram import Bot, Dispatcher
from app.config import BOT_TOKEN
from app import db
from app.handlers import start as h_start
from app.handlers import notes as h_notes
from app.handlers import schedule as h_schedule
from app.handlers import calc as h_calc
from app.scheduler import start_scheduler, reload_all_jobs

async def on_startup(bot: Bot):
    db.init_db()
    start_scheduler()
    # восстановим напоминания из БД
    reload_all_jobs(bot)

async def main():
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN не найден в .env")
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()

    # Регистрация роутеров
    dp.include_router(h_start.router)
    dp.include_router(h_notes.router)
    dp.include_router(h_schedule.router)
    dp.include_router(h_calc.router)

    await on_startup(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
