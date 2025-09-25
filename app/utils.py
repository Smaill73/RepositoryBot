from datetime import datetime, timedelta

ISO_FMT = "%Y-%m-%d %H:%M"

def parse_user_datetime(s:str) -> datetime:
    # Ожидаем "YYYY-MM-DD HH:MM"
    return datetime.strptime(s.strip(), ISO_FMT)

def day_bounds(dt:datetime):
    start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start, end

def week_bounds(dt:datetime):
    # неделя от понедельника
    start = dt - timedelta(days=dt.weekday())
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=7)
    return start, end
