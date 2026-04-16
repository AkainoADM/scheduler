import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.reference import Calendar
from app.schemas.calendar import CalendarCreate
from datetime import date, timedelta
from typing import List, Dict, Any
from sqlalchemy import update

API_URL = "https://calendar.kuzyak.in/api/calendar/{year}"

# Известные праздники (можно расширить)
HOLIDAYS = {
    (1, 1): "Новогодние каникулы",
    (1, 2): "Новогодние каникулы",
    (1, 3): "Новогодние каникулы",
    (1, 4): "Новогодние каникулы",
    (1, 5): "Новогодние каникулы",
    (1, 6): "Новогодние каникулы",
    (1, 7): "Рождество Христово",
    (2, 23): "День защитника Отечества",
    (3, 8): "Международный женский день",
    (5, 1): "Праздник Весны и Труда",
    (5, 9): "День Победы",
    (6, 12): "День России",
    (11, 4): "День народного единства",
}

async def fetch_calendar_data(year: int) -> Dict[str, Any]:
    url = API_URL.format(year=year)
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()
        print(f"API ответ для {year}: {len(data.get('days', {}))} дней")
        if data.get('days'):
            days = list(data.get('days', {}).items())[:3]
            print(f"Примеры: {days}")
        return data

def parse_api_response(data: Dict[str, Any]) -> List[CalendarCreate]:
    entries = []
    for date_str, day_info in data.get('days', {}).items():
        is_working = day_info.get('isWorking', 0) == 0
        description = None
        if not is_working:
            description = day_info.get('name')
            if day_info.get('isWorking') == 3:
                description = "Сокращенный день"
        entries.append(CalendarCreate(
            date=date.fromisoformat(date_str),
            is_working_day=is_working,
            description=description
        ))
    print(f"Сформировано {len(entries)} записей из API")
    return entries

def generate_calendar_locally(year: int) -> List[CalendarCreate]:
    """Генерирует календарь на основе правил: выходные - суббота и воскресенье, плюс праздники"""
    entries = []
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    current = start_date
    while current <= end_date:
        is_working = current.weekday() < 5  # понедельник=0, воскресенье=6 -> 0-4 рабочие
        description = None
        # Проверяем, является ли дата праздником
        if (current.month, current.day) in HOLIDAYS:
            is_working = False
            description = HOLIDAYS[(current.month, current.day)]
        entries.append(CalendarCreate(
            date=current,
            is_working_day=is_working,
            description=description
        ))
        current += timedelta(days=1)
    print(f"Сгенерировано {len(entries)} записей локально для {year}")
    return entries

async def update_calendar_db(db: AsyncSession, entries: List[CalendarCreate]) -> Dict[str, int]:
    added = 0
    updated = 0
    for entry in entries:
        # пытаемся обновить существующую запись через SQL UPDATE
        stmt = update(Calendar).where(Calendar.date == entry.date).values(
            is_working_day=entry.is_working_day,
            description=entry.description
        ).execution_options(synchronize_session="fetch")
        result = await db.execute(stmt)
        # result.rowcount может быть None в некоторых драйверах, поэтому проверяем безопасно
        rowcount = getattr(result, "rowcount", None)
        if rowcount and rowcount > 0:
            updated += 1
        else:
            db.add(Calendar(**entry.model_dump()))
            added += 1
    await db.commit()
    return {"added": added, "updated": updated}


async def sync_calendar_for_year(year: int) -> Dict[str, Any]:
    try:
        # Пытаемся получить данные из API
        data = await fetch_calendar_data(year)
        if data.get('days'):
            entries = parse_api_response(data)
        else:
            print(f"API не вернул данные для {year}, генерируем локально")
            entries = generate_calendar_locally(year)
    except Exception as e:
        print(f"Ошибка API, генерируем локально: {e}")
        entries = generate_calendar_locally(year)

    async with AsyncSessionLocal() as db:
        result = await update_calendar_db(db, entries)
    print(f"Синхронизация за {year}: добавлено {result['added']}, обновлено {result['updated']}")
    return {"year": year, **result, "status": "success"}