from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.services import day_of_week as service
from app.schemas.day_of_week import DayOfWeekCreate, DayOfWeekResponse, DayOfWeekUpdate

router = APIRouter(prefix="/days-of-week", tags=["Days of Week"])

@router.get("/", response_model=List[DayOfWeekResponse])
async def read_all(db: AsyncSession = Depends(get_db)):
    return await service.get_all_days_of_week(db)

@router.get("/{dow_id}", response_model=DayOfWeekResponse)
async def read_one(dow_id: int, db: AsyncSession = Depends(get_db)):
    item = await service.get_day_of_week(db, dow_id)
    if not item:
        raise HTTPException(status_code=404, detail="Day of week not found")
    return item

@router.post("/", response_model=DayOfWeekResponse)
async def create(data: DayOfWeekCreate, db: AsyncSession = Depends(get_db)):
    return await service.create_day_of_week(db, data)

@router.put("/{dow_id}", response_model=DayOfWeekResponse)
async def update(dow_id: int, data: DayOfWeekUpdate, db: AsyncSession = Depends(get_db)):
    item = await service.update_day_of_week(db, dow_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Day of week not found")
    return item

@router.delete("/{dow_id}")
async def delete(dow_id: int, db: AsyncSession = Depends(get_db)):
    await service.delete_day_of_week(db, dow_id)
    return {"ok": True}

@router.post("/bulk-delete")
async def bulk_delete(ids: List[int], db: AsyncSession = Depends(get_db)):
    await service.bulk_delete_days_of_week(db, ids)
    return {"ok": True}