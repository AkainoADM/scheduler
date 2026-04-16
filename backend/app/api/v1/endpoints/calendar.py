from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import calendar as service
from app.schemas.calendar import CalendarCreate, CalendarResponse, CalendarUpdate
from typing import List

from fastapi import UploadFile, File
from app.services import excel_import

router = APIRouter(prefix="/calendar", tags=["Calendar"])

@router.get("/", response_model=list[CalendarResponse])
async def read_calendar(db: AsyncSession = Depends(get_db)):
    return await service.get_all_calendar(db)

@router.get("/{entry_id}", response_model=CalendarResponse)
async def read_calendar_entry(entry_id: int, db: AsyncSession = Depends(get_db)):
    entry = await service.get_calendar_entry(db, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry

@router.post("/", response_model=CalendarResponse)
async def create_calendar_entry(data: CalendarCreate, db: AsyncSession = Depends(get_db)):
    return await service.create_calendar_entry(db, data)

@router.put("/{entry_id}", response_model=CalendarResponse)
async def update_calendar_entry(entry_id: int, data: CalendarUpdate, db: AsyncSession = Depends(get_db)):
    entry = await service.update_calendar_entry(db, entry_id, data)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry

@router.delete("/{entry_id}")
async def delete_calendar_entry(entry_id: int, db: AsyncSession = Depends(get_db)):
    await service.delete_calendar_entry(db, entry_id)
    return {"ok": True}

@router.post("/bulk-delete")
async def bulk_delete_calendar(ids: List[int], db: AsyncSession = Depends(get_db)):
    await service.bulk_delete_calendar(db, ids)
    return {"ok": True}

@router.post("/upload", summary="Загрузить календарь из Excel")
async def upload_calendar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "Файл должен быть Excel (.xlsx или .xls)")
    try:
        content = await file.read()
        rows = await excel_import.parse_calendar_excel(content)
    except Exception as e:
        raise HTTPException(400, f"Ошибка чтения файла: {str(e)}")
    valid, errors = await excel_import.validate_calendar_data(rows, db)
    result = await excel_import.save_calendar_from_validated(valid, db)
    return {
        "message": "Загрузка завершена",
        "added": result["added"],
        "updated": result["updated"],
        "errors": errors
    }