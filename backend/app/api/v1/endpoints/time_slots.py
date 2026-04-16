from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import time_slot as service
from app.schemas.time_slot import TimeSlotCreate, TimeSlotResponse, TimeSlotUpdate
from typing import List

router = APIRouter(prefix="/time-slots", tags=["TimeSlots"])

@router.get("/", response_model=list[TimeSlotResponse])
async def read_time_slots(db: AsyncSession = Depends(get_db)):
    return await service.get_all_time_slots(db)

@router.get("/{ts_id}", response_model=TimeSlotResponse)
async def read_time_slot(ts_id: int, db: AsyncSession = Depends(get_db)):
    ts = await service.get_time_slot(db, ts_id)
    if not ts:
        raise HTTPException(status_code=404, detail="TimeSlot not found")
    return ts

@router.post("/", response_model=TimeSlotResponse)
async def create_time_slot(data: TimeSlotCreate, db: AsyncSession = Depends(get_db)):
    return await service.create_time_slot(db, data)

@router.put("/{ts_id}", response_model=TimeSlotResponse)
async def update_time_slot(ts_id: int, data: TimeSlotUpdate, db: AsyncSession = Depends(get_db)):
    ts = await service.update_time_slot(db, ts_id, data)
    if not ts:
        raise HTTPException(status_code=404, detail="TimeSlot not found")
    return ts

@router.delete("/{ts_id}")
async def delete_time_slot(ts_id: int, db: AsyncSession = Depends(get_db)):
    await service.delete_time_slot(db, ts_id)
    return {"ok": True}

@router.post("/bulk-delete")
async def bulk_delete_time_slots(ids: List[int], db: AsyncSession = Depends(get_db)):
    await service.bulk_delete_time_slots(db, ids)
    return {"ok": True}

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.services import time_slot as time_slot_service
from app.services import excel_import
from app.schemas.time_slot import TimeSlotCreate, TimeSlotResponse, TimeSlotUpdate

router = APIRouter(prefix="/time-slots", tags=["Time Slots"])

@router.get("/", response_model=List[TimeSlotResponse])
async def read_time_slots(db: AsyncSession = Depends(get_db)):
    return await time_slot_service.get_all_time_slots(db)

@router.get("/{ts_id}", response_model=TimeSlotResponse)
async def read_time_slot(ts_id: int, db: AsyncSession = Depends(get_db)):
    ts = await time_slot_service.get_time_slot(db, ts_id)
    if not ts:
        raise HTTPException(status_code=404, detail="Time slot not found")
    return ts

@router.post("/", response_model=TimeSlotResponse)
async def create_time_slot(data: TimeSlotCreate, db: AsyncSession = Depends(get_db)):
    return await time_slot_service.create_time_slot(db, data)

@router.put("/{ts_id}", response_model=TimeSlotResponse)
async def update_time_slot(ts_id: int, data: TimeSlotUpdate, db: AsyncSession = Depends(get_db)):
    ts = await time_slot_service.update_time_slot(db, ts_id, data)
    if not ts:
        raise HTTPException(status_code=404, detail="Time slot not found")
    return ts

@router.delete("/{ts_id}")
async def delete_time_slot(ts_id: int, db: AsyncSession = Depends(get_db)):
    await time_slot_service.delete_time_slot(db, ts_id)
    return {"ok": True}

@router.post("/bulk-delete")
async def bulk_delete_time_slots(ids: List[int], db: AsyncSession = Depends(get_db)):
    await time_slot_service.bulk_delete_time_slots(db, ids)
    return {"ok": True}

@router.post("/upload", summary="Загрузить временные слоты из Excel")
async def upload_time_slots(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "Файл должен быть Excel (.xlsx или .xls)")
    try:
        content = await file.read()
        rows = await excel_import.parse_time_slots_excel(content)
    except Exception as e:
        raise HTTPException(400, f"Ошибка чтения файла: {str(e)}")
    valid, errors = await excel_import.validate_time_slots_data(rows, db)
    result = await excel_import.save_time_slots_from_validated(valid, db)
    return {
        "message": "Загрузка завершена",
        "added": result["added"],
        "updated": result["updated"],
        "errors": errors
    }