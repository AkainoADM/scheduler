from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import calendar as calendar_service
from app.services import calendar_sync
from app.schemas.calendar import CalendarCreate, CalendarResponse, CalendarUpdate

router = APIRouter(prefix="/calendar", tags=["Calendar"])

@router.get("/", response_model=list[CalendarResponse])
async def read_calendar(db: AsyncSession = Depends(get_db)):
    return await calendar_service.get_all_calendar(db)

@router.get("/{entry_id}", response_model=CalendarResponse)
async def read_calendar_entry(entry_id: int, db: AsyncSession = Depends(get_db)):
    entry = await calendar_service.get_calendar_entry(db, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return entry

@router.post("/", response_model=CalendarResponse)
async def create_calendar_entry(data: CalendarCreate, db: AsyncSession = Depends(get_db)):
    return await calendar_service.create_calendar_entry(db, data)

@router.put("/{entry_id}", response_model=CalendarResponse)
async def update_calendar_entry(entry_id: int, data: CalendarUpdate, db: AsyncSession = Depends(get_db)):
    entry = await calendar_service.update_calendar_entry(db, entry_id, data)
    if not entry:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return entry

@router.delete("/{entry_id}")
async def delete_calendar_entry(entry_id: int, db: AsyncSession = Depends(get_db)):
    await calendar_service.delete_calendar_entry(db, entry_id)
    return {"ok": True}

@router.post("/sync/{year}")
async def sync_calendar(year: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """
    Запускает синхронизацию календаря за указанный год в фоновом режиме.
    """
    background_tasks.add_task(calendar_sync.sync_calendar_for_year, db, year)
    return {"message": f"Синхронизация календаря за {year} год запущена в фоновом режиме"}