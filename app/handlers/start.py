from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

@router.message(Command("start"))
async def cmd_start(m: Message):
    await m.answer(
        "Привет! Я упрощённый студенческий помощник.\n\n"
        "📌 Заметки и медиа:\n"
        "  /newnote — создать диалогом\n"
        "  Просто пришли текст/фото/видео/голос — сохраню как заметку\n"
        "  /notes — посмотреть заметки (с пагинацией)\n"
        "  /find <слово> — поиск\n\n"
        "🗓 Расписание:\n"
        "  /addevent — добавить событие (диалогом)\n"
        "  /today — события на сегодня\n"
        "  /week — события на неделю\n\n"
        "🧮 Калькулятор:\n"
        "  /gpa 5 4 3 — средний балл\n"
        "  /percent <сумма> <годовая_%> <месяцев>\n"
        "Подсказка: дату вводи в формате YYYY-MM-DD HH:MM"
    )

@router.message(Command("help"))
async def cmd_help(m: Message):
    await m.answer("Нужна помощь? Пиши, что хочешь сделать, или используй команды из /start")
