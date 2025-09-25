from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from pathlib import Path
from ...app import db  # for relative safety if __package__ differs — we'll import absolute below
# (ниже используем абсолютный импорт для надёжности)
from app import db
from app.keyboards.common import notes_list_kb, note_actions_kb

router = Router()

# ---------- FSM ----------
class NoteCreate(StatesGroup):
    title = State()
    content = State()

@router.message(Command("newnote"))
async def newnote(m: Message, state: FSMContext):
    await state.set_state(NoteCreate.title)
    await m.answer("Введи заголовок заметки:")

@router.message(NoteCreate.title, F.text.len() > 0)
async def note_title(m: Message, state: FSMContext):
    await state.update_data(title=m.text.strip())
    await state.set_state(NoteCreate.content)
    await m.answer("Теперь пришли текст заметки или медиа (фото/видео/документ/голос).")

@router.message(NoteCreate.content, F.content_type.in_({"text","photo","video","voice","video_note","document"}))
async def note_content(m: Message, state: FSMContext):
    data = await state.get_data()
    title = data.get("title")
    text, file_path, file_type = None, None, None

    if m.text:
        text = m.text

    user_dir = Path("data")/str(m.from_user.id)
    user_dir.mkdir(parents=True, exist_ok=True)

    bot = m.bot
    if m.photo:
        file = await bot.get_file(m.photo[-1].file_id)
        fp = user_dir / f"photo_{file.file_unique_id}.jpg"
        await bot.download(file, destination=fp); file_path=str(fp); file_type="photo"
    elif m.video:
        file = await bot.get_file(m.video.file_id)
        fp = user_dir / f"video_{file.file_unique_id}.mp4"
        await bot.download(file, destination=fp); file_path=str(fp); file_type="video"
    elif m.voice:
        file = await bot.get_file(m.voice.file_id)
        fp = user_dir / f"voice_{file.file_unique_id}.ogg"
        await bot.download(file, destination=fp); file_path=str(fp); file_type="voice"
    elif m.video_note:
        file = await bot.get_file(m.video_note.file_id)
        fp = user_dir / f"vnote_{file.file_unique_id}.mp4"
        await bot.download(file, destination=fp); file_path=str(fp); file_type="video_note"
    elif m.document:
        file = await bot.get_file(m.document.file_id)
        name = m.document.file_name or f"doc_{file.file_unique_id}.bin"
        fp = user_dir / name
        await bot.download(file, destination=fp); file_path=str(fp); file_type="document"

    nid = db.add_note(m.from_user.id, title, text, file_path, file_type)
    await state.clear()
    await m.answer(f"✅ Заметка сохранена (id: {nid}).", reply_markup=note_actions_kb(nid))

# ---------- Быстрое создание: просто пришли что-то ----------
@router.message(F.content_type.in_({"text","photo","video","voice","video_note","document"}))
async def quick_note(m: Message):
    # Сохраняем «на лету», если это не команда
    if m.text and m.text.startswith("/"):
        return

    title, text = None, None
    if m.text:
        parts = m.text.split("\n\n", 1)
        title = parts[0][:80]
        text = parts[1] if len(parts) > 1 else m.text

    user_dir = Path("data")/str(m.from_user.id)
    user_dir.mkdir(parents=True, exist_ok=True)

    bot = m.bot
    file_path, file_type = None, None

    if m.photo:
        file = await bot.get_file(m.photo[-1].file_id)
        fp = user_dir / f"photo_{file.file_unique_id}.jpg"
        await bot.download(file, destination=fp); file_path=str(fp); file_type="photo"
    elif m.video:
        file = await bot.get_file(m.video.file_id)
        fp = user_dir / f"video_{file.file_unique_id}.mp4"
        await bot.download(file, destination=fp); file_path=str(fp); file_type="video"
    elif m.voice:
        file = await bot.get_file(m.voice.file_id)
        fp = user_dir / f"voice_{file.file_unique_id}.ogg"
        await bot.download(file, destination=fp); file_path=str(fp); file_type="voice"
    elif m.video_note:
        file = await bot.get_file(m.video_note.file_id)
        fp = user_dir / f"vnote_{file.file_unique_id}.mp4"
        await bot.download(file, destination=fp); file_path=str(fp); file_type="video_note"
    elif m.document:
        file = await bot.get_file(m.document.file_id)
        name = m.document.file_name or f"doc_{file.file_unique_id}.bin"
        fp = user_dir / name
        await bot.download(file, destination=fp); file_path=str(fp); file_type="document"

    nid = db.add_note(m.from_user.id, title, text, file_path, file_type)
    await m.answer(f"✅ Заметка сохранена (id: {nid}).", reply_markup=note_actions_kb(nid))

# ---------- Список, поиск, удаление ----------
PAGE_SIZE = 5

@router.message(Command("notes"))
async def list_notes_cmd(m: Message):
    await send_notes_page(m, page=0)

async def send_notes_page(m: Message, page:int):
    total = db.count_notes(m.from_user.id)
    offset = page * PAGE_SIZE
    rows = db.list_notes(m.from_user.id, offset=offset, limit=PAGE_SIZE)
    if not rows:
        await m.answer("Пока нет заметок.")
        return
    lines = [f"#{r['id']} • {r['title'] or 'без заголовка'}" for r in rows]
    has_prev = page > 0
    has_next = offset + PAGE_SIZE < total
    await m.answer("\n".join(lines), reply_markup=notes_list_kb(page, has_prev, has_next))

@router.callback_query(F.data.startswith("notes_page:"))
async def notes_page_cb(c: CallbackQuery):
    page = int(c.data.split(":")[1])
    await c.message.edit_text("Загрузка...")
    await send_notes_page(c.message, page)
    await c.answer()

@router.message(Command("find"))
async def find_notes(m: Message):
    args = (m.text or "").split(maxsplit=1)
    if len(args) < 2:
        return await m.answer("Использование: /find <слово>")
    q = args[1].strip()
    rows = db.search_notes(m.from_user.id, q, limit=10)
    if not rows:
        return await m.answer("Ничего не найдено.")
    msg = "\n".join([f"#{r['id']} • {r['title'] or 'без заголовка'}" for r in rows])
    await m.answer(msg)

@router.message(Command("delnote"))
async def delnote_cmd(m: Message):
    args = (m.text or "").split(maxsplit=1)
    if len(args) < 2:
        return await m.answer("Использование: /delnote <id>")
    try:
        nid = int(args[1])
    except:
        return await m.answer("id должен быть числом.")
    ok = db.delete_note(m.from_user.id, nid)
    await m.answer("🗑 Удалено." if ok else "Не найдено.")

@router.callback_query(F.data.startswith("delnote:"))
async def delnote_cb(c: CallbackQuery):
    nid = int(c.data.split(":")[1])
    ok = db.delete_note(c.from_user.id, nid)
    await c.answer("Удалено." if ok else "Не найдено.", show_alert=False)
    try:
        await c.message.delete()
    except:
        pass
