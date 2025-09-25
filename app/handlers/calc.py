from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

@router.message(Command("gpa"))
async def gpa(m: Message):
    try:
        parts = (m.text or "").split()[1:]
        grades = [float(x.replace(",", ".")) for x in parts]
        if not grades: raise ValueError
        g = sum(grades)/len(grades)
        await m.answer(f"🎓 Средний балл: {g:.2f}")
    except:
        await m.answer("Использование: /gpa 5 4 4 3")

@router.message(Command("percent"))
async def percent(m: Message):
    # Аннуитетный платёж: /percent <сумма> <годовая_%> <месяцев>
    try:
        parts = (m.text or "").split()[1:]
        S, r_year, n = float(parts[0]), float(parts[1]), float(parts[2])
        r_m = r_year/12/100
        pmt = S * (r_m*(1+r_m)**n)/(((1+r_m)**n)-1)
        over = pmt*n - S
        await m.answer(f"💰 Платёж/мес: {pmt:.2f}\nПереплата: {over:.2f}")
    except:
        await m.answer("Использование: /percent <сумма> <годовая_%> <месяцев>")
