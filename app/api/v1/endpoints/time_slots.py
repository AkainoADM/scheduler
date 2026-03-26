from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import time_slot as time_slot_service
from app.schemas.time_slot import TimeSlotCreate, TimeSlotResponse, TimeSlotUpdate

router = APIRouter(prefix="/time_slots", tags=["Time Slots"])

@router.get("/", response_model=list[TimeSlotResponse])
async def read_time_slots(db: AsyncSession = Depends(get_db)):
    return await time_slot_service.get_all_time_slots(db)

@router.get("/{slot_id}", response_model=TimeSlotResponse)
async def read_time_slot(slot_id: int, db: AsyncSession = Depends(get_db)):
    slot = await time_slot_service.get_time_slot(db, slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Time slot not found")
    return slot

@router.post("/", response_model=TimeSlotResponse)
async def create_time_slot(data: TimeSlotCreate, db: AsyncSession = Depends(get_db)):
    return await time_slot_service.create_time_slot(db, data)

@router.put("/{slot_id}", response_model=TimeSlotResponse)
async def update_time_slot(slot_id: int, data: TimeSlotUpdate, db: AsyncSession = Depends(get_db)):
    slot = await time_slot_service.update_time_slot(db, slot_id, data)
    if not slot:
        raise HTTPException(status_code=404, detail="Time slot not found")
    return slot

@router.delete("/{slot_id}")
async def delete_time_slot(slot_id: int, db: AsyncSession = Depends(get_db)):
    await time_slot_service.delete_time_slot(db, slot_id)
    return {"ok": True}