from aiogram.utils.keyboard import InlineKeyboardBuilder

def notes_list_kb(page:int, has_prev:bool, has_next:bool):
    kb = InlineKeyboardBuilder()
    if has_prev:
        kb.button(text="⬅️ Назад", callback_data=f"notes_page:{page-1}")
    if has_next:
        kb.button(text="Вперёд ➡️", callback_data=f"notes_page:{page+1}")
    kb.adjust(2)
    return kb.as_markup()

def note_actions_kb(note_id:int):
    kb = InlineKeyboardBuilder()
    kb.button(text="🗑 Удалить", callback_data=f"delnote:{note_id}")
    return kb.as_markup()

def events_list_kb():
    # можно расширить под пагинацию событий
    return InlineKeyboardBuilder().as_markup()

def event_actions_kb(event_id:int):
    kb = InlineKeyboardBuilder()
    kb.button(text="🗑 Удалить", callback_data=f"delevent:{event_id}")
    return kb.as_markup()
