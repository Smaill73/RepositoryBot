from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from datetime import datetime
from app import db
from app.utils import parse_user_datetime, day_bounds, week_bounds
from app.keyboards.common import event_actions_kb
from app.scheduler import schedule_event_notification, unschedule_event

router = Router()

# ---------- FSM ----------
class EventCreate(StatesGroup):
    title = State()
    when_dt = State()
    remind = State()

@router.message(Command("addevent"))
async def addevent_start(m: Message, state: FSMContext):
    await state.set_state(EventCreate.title)
    await m.answer("Название события:")

@router.message(EventCreate.title, F.text.len() > 0)
async def addevent_title(m: Message, state: FSMContext):
    await state.update_data(title=m.text.strip())
    await state.set_state(EventCreate.when_dt)
    await m.answer("Когда? Формат: YYYY-MM-DD HH:MM")

@router.message(EventCreate.when_dt, F.text.len() > 0)
async def addevent_when(m: Message, state: FSMContext):
    try:
        dt = parse_user_datetime(m.text)
    except Exception:
        return await m.answer("Неверный формат. Пример: 2025-09-30 10:00")
    await state.update_data(when_dt=dt)
    await state.set_state(EventCreate.remind)
    await m.answer("За сколько минут напомнить? (например, 30)")

@router.message(EventCreate.remind, F.text.len() > 0)
async def addevent_finish(m: Message, state: FSMContext):
    try:
        remind = int(m.text.strip())
    except Exception:
        return await m.answer("Нужно число минут, например 30.")
    data = await state.get_data()
    title: str = data["title"]
    when_dt: datetime = data["when_dt"]
    ev_id = db.add_event(m.from_user.id, title, when_dt.isoformat(), remind)
    await state.clear()
    row = db.get_event(ev_id)
    # регистрация напоминания
    schedule_event_notification(m.bot, row)
    await m.answer(f"✅ Событие #{ev_id}: {title}\nВремя: {when_dt}\nНапоминание за {remind} мин.",
                   reply_markup=event_actions_kb(ev_id))

@router.message(Command("today"))
async def today(m: Message):
    start, end = day_bounds(datetime.now())
    rows = db.list_events_between(m.from_user.id, start.isoformat(), end.isoformat())
    if not rows:
        return await m.answer("На сегодня событий нет.")
    txt = "\n".join([f"#{r['id']} • {r['title']} — {r['when_dt']}" for r in rows])
    await m.answer(txt)

@router.message(Command("week"))
async def week(m: Message):
    start, end = week_bounds(datetime.now())
    rows = db.list_events_between(m.from_user.id, start.isoformat(), end.isoformat())
    if not rows:
        return await m.answer("На этой неделе событий нет.")
    txt = "\n".join([f"#{r['id']} • {r['title']} — {r['when_dt']}" for r in rows])
    await m.answer(txt)

@router.message(Command("delevent"))
async def delevent_cmd(m: Message):
    args = (m.text or "").split(maxsplit=1)
    if len(args) < 2: return await m.answer("Использование: /delevent <id>")
    try:
        ev_id = int(args[1])
    except:
        return await m.answer("id должен быть числом.")
    ok = db.delete_event(m.from_user.id, ev_id)
    if ok:
        unschedule_event(ev_id)
    await m.answer("🗑 Удалено." if ok else "Не найдено.")

@router.callback_query(F.data.startswith("delevent:"))
async def delevent_cb(c: CallbackQuery):
    ev_id = int(c.data.split(":")[1])
    ok = db.delete_event(c.from_user.id, ev_id)
    if ok:
        unschedule_event(ev_id)
    await c.answer("Удалено." if ok else "Не найдено.", show_alert=False)
    try:
        await c.message.delete()
    except:
        pass
