import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent.parent / "bot.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS notes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER NOT NULL,
            title TEXT,
            text TEXT,
            file_path TEXT,
            file_type TEXT,
            created_at TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS events(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            when_dt TEXT NOT NULL,
            remind_before_min INTEGER DEFAULT 30
        )""")

# ---------- NOTES ----------
def add_note(tg_id:int, title:str|None, text:str|None,
             file_path:str|None, file_type:str|None) -> int:
    with get_conn() as c:
        c.execute("""INSERT INTO notes(tg_id,title,text,file_path,file_type,created_at)
                     VALUES(?,?,?,?,?,?)""",
                  (tg_id, title, text, file_path, file_type,
                   datetime.now().isoformat()))
        return c.lastrowid

def list_notes(tg_id:int, offset:int=0, limit:int=10):
    with get_conn() as c:
        cur = c.execute("""SELECT * FROM notes
                           WHERE tg_id=?
                           ORDER BY id DESC
                           LIMIT ? OFFSET ?""",
                        (tg_id, limit, offset))
        return cur.fetchall()

def count_notes(tg_id:int) -> int:
    with get_conn() as c:
        cur = c.execute("SELECT COUNT(*) AS n FROM notes WHERE tg_id=?", (tg_id,))
        return cur.fetchone()["n"]

def search_notes(tg_id:int, q:str, limit:int=10):
    like = f"%{q}%"
    with get_conn() as c:
        cur = c.execute("""SELECT * FROM notes
                           WHERE tg_id=? AND (text LIKE ? OR title LIKE ?)
                           ORDER BY id DESC LIMIT ?""",
                        (tg_id, like, like, limit))
        return cur.fetchall()

def delete_note(tg_id:int, note_id:int) -> bool:
    with get_conn() as c:
        cur = c.execute("DELETE FROM notes WHERE tg_id=? AND id=?", (tg_id, note_id))
        return cur.rowcount > 0

# ---------- EVENTS ----------
def add_event(tg_id:int, title:str, when_dt_iso:str, remind_before:int=30) -> int:
    with get_conn() as c:
        c.execute("""INSERT INTO events(tg_id,title,when_dt,remind_before_min)
                     VALUES(?,?,?,?)""",
                  (tg_id, title, when_dt_iso, remind_before))
        return c.lastrowid

def get_event(event_id:int):
    with get_conn() as c:
        cur = c.execute("SELECT * FROM events WHERE id=?", (event_id,))
        return cur.fetchone()

def delete_event(tg_id:int, event_id:int) -> bool:
    with get_conn() as c:
        cur = c.execute("DELETE FROM events WHERE tg_id=? AND id=?", (tg_id, event_id))
        return cur.rowcount > 0

def list_events_between(tg_id:int, start_iso:str, end_iso:str):
    with get_conn() as c:
        cur = c.execute("""SELECT * FROM events
                           WHERE tg_id=? AND when_dt BETWEEN ? AND ?
                           ORDER BY when_dt""",
                        (tg_id, start_iso, end_iso))
        return cur.fetchall()

def list_all_upcoming(now_iso:str):
    with get_conn() as c:
        cur = c.execute("""SELECT * FROM events
                           WHERE when_dt > ?
                           ORDER BY when_dt""",
                        (now_iso,))
        return cur.fetchall()
