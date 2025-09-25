from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.base import ConflictingIdError
from aiogram import Bot
from . import db

# Один общий планировщик на процесс
scheduler: AsyncIOScheduler | None = None

def get_scheduler() -> AsyncIOScheduler:
    global scheduler
    if scheduler is None:
        scheduler = AsyncIOScheduler(timezone=None)  # системное время
    return scheduler

def _job_id(event_id:int) -> str:
    return f"event_notify_{event_id}"

async def send_event_reminder(bot: Bot, tg_id:int, title:str, when_dt_str:str):
    msg = f"⏰ Напоминание: {title}\nВремя: {when_dt_str}"
    try:
        await bot.send_message(tg_id, msg)
    except Exception:
        # можно логировать ошибки доставки
        pass

def schedule_event_notification(bot: Bot, event_row):
    """
    Регистрирует задачу напоминания для события.
    event_row: sqlite Row с полями (id, tg_id, title, when_dt, remind_before_min)
    """
    sch = get_scheduler()

    when_dt = datetime.fromisoformat(event_row["when_dt"])
    run_at = when_dt - timedelta(minutes=int(event_row["remind_before_min"] or 30))
    if run_at <= datetime.now():
        # если время напоминания уже прошло — можно проигнорировать или отправить сразу
        return

    job_id = _job_id(event_row["id"])
    try:
        sch.add_job(
            send_event_reminder,
            "date",
            id=job_id,
            run_date=run_at,
            args=[bot, event_row["tg_id"], event_row["title"], event_row["when_dt"]],
            replace_existing=True,
            misfire_grace_time=60  # если чуть опоздали — всё равно отправим
        )
    except ConflictingIdError:
        # уже есть — заменим
        sch.remove_job(job_id)
        sch.add_job(
            send_event_reminder, "date",
            id=job_id, run_date=run_at,
            args=[bot, event_row["tg_id"], event_row["title"], event_row["when_dt"]],
            replace_existing=True,
            misfire_grace_time=60
        )

def unschedule_event(event_id:int):
    sch = get_scheduler()
    job_id = _job_id(event_id)
    try:
        sch.remove_job(job_id)
    except Exception:
        pass

def start_scheduler():
    sch = get_scheduler()
    if not sch.running:
        sch.start()

def reload_all_jobs(bot: Bot):
    """Перерегистрировать все будущие события из БД при старте бота."""
    now_iso = datetime.now().isoformat()
    rows = db.list_all_upcoming(now_iso)
    for r in rows:
        schedule_event_notification(bot, r)
