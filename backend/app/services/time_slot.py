from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.reference import TimeSlot
from app.schemas.time_slot import TimeSlotCreate, TimeSlotUpdate
from typing import List

async def get_all_time_slots(db: AsyncSession):
    result = await db.execute(select(TimeSlot).order_by(TimeSlot.slot_number))
    return result.scalars().all()

async def get_time_slot(db: AsyncSession, ts_id: int):
    result = await db.execute(select(TimeSlot).where(TimeSlot.id == ts_id))
    return result.scalar_one_or_none()

async def create_time_slot(db: AsyncSession, data: TimeSlotCreate) -> TimeSlot:
    ts = TimeSlot(**data.model_dump())
    db.add(ts)
    await db.commit()
    await db.refresh(ts)
    return ts

async def update_time_slot(db: AsyncSession, ts_id: int, data: TimeSlotUpdate) -> TimeSlot | None:
    stmt = update(TimeSlot).where(TimeSlot.id == ts_id).values(**data.model_dump(exclude_unset=True)).returning(TimeSlot)
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one_or_none()

async def delete_time_slot(db: AsyncSession, ts_id: int) -> None:
    await db.execute(delete(TimeSlot).where(TimeSlot.id == ts_id))
    await db.commit()

async def bulk_delete_time_slots(db: AsyncSession, ids: List[int]) -> None:
    await db.execute(delete(TimeSlot).where(TimeSlot.id.in_(ids)))
    await db.commit()