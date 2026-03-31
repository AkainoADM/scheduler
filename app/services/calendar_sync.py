import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.reference import Calendar
from app.schemas.calendar import CalendarCreate
from datetime import date, timedelta
from typing import List, Dict, Any

# URL API, который будет возвращать данные за указанный год
API_URL = "https://calendar.kuzyak.in/api/calendar/{year}"

async def fetch_calendar_data(year: int) -> Dict[str, Any]:
    """
    Получает данные производственного календаря за указанный год.
    """
    url = API_URL.format(year=year)
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()

def parse_api_response(data: Dict[str, Any]) -> List[CalendarCreate]:
    """
    Преобразует ответ от API в список объектов CalendarCreate.
    """
    calendar_entries = []
    # В ответе API в ключе 'days' хранится объект с датами в формате YYYY-MM-DD
    for date_str, day_info in data.get('days', {}).items():
        # Определяем, является ли день рабочим
        # В API: isWorking = 0 (рабочий), 2 (нерабочий/праздник), 3 (сокращенный)
        # В нашей БД: is_working_day = True (рабочий), False (нерабочий)
        is_working = day_info.get('isWorking', 0) == 0

        # Получаем описание праздника, если день нерабочий
        description = None
        if not is_working:
            description = day_info.get('name')
            if day_info.get('isWorking') == 3:
                description = "Сокращенный день"

        # Создаем объект для вставки/обновления
        entry = CalendarCreate(
            date=date.fromisoformat(date_str),
            is_working_day=is_working,
            description=description
            # Поля week_type пока не заполняем, но в будущем их можно добавить
        )
        calendar_entries.append(entry)
    return calendar_entries

async def update_calendar_db(db: AsyncSession, entries: List[CalendarCreate]) -> Dict[str, int]:
    """
    Обновляет или создает записи в таблице calendar.
    Возвращает количество добавленных и обновленных записей.
    """
    added = 0
    updated = 0
    for entry in entries:
        # Проверяем, существует ли уже запись с такой датой
        stmt = select(Calendar).where(Calendar.date == entry.date)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Обновляем существующую запись
            existing.is_working_day = entry.is_working_day
            existing.description = entry.description
            updated += 1
        else:
            # Создаем новую
            new_entry = Calendar(**entry.model_dump())
            db.add(new_entry)
            added += 1
    await db.commit()
    return {"added": added, "updated": updated}

async def sync_calendar_for_year(db: AsyncSession, year: int) -> Dict[str, Any]:
    """
    Основная функция: загружает календарь за год и сохраняет в БД.
    """
    try:
        data = await fetch_calendar_data(year)
        entries = parse_api_response(data)
        result = await update_calendar_db(db, entries)
        return {"year": year, **result, "status": "success"}
    except Exception as e:
        return {"year": year, "status": "error", "message": str(e)}