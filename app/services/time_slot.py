from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.reference import TimeSlot
from app.schemas.time_slot import TimeSlotCreate, TimeSlotUpdate

async def get_all_time_slots(db: AsyncSession):
    result = await db.execute(select(TimeSlot))
    return result.scalars().all()

async def get_time_slot(db: AsyncSession, slot_id: int):
    result = await db.execute(select(TimeSlot).where(TimeSlot.id == slot_id))
    return result.scalar_one_or_none()

async def create_time_slot(db: AsyncSession, data: TimeSlotCreate) -> TimeSlot:
    slot = TimeSlot(**data.model_dump())
    db.add(slot)
    await db.commit()
    await db.refresh(slot)
    return slot

async def update_time_slot(db: AsyncSession, slot_id: int, data: TimeSlotUpdate) -> TimeSlot | None:
    stmt = update(TimeSlot).where(TimeSlot.id == slot_id).values(**data.model_dump(exclude_unset=True)).returning(TimeSlot)
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one_or_none()

async def delete_time_slot(db: AsyncSession, slot_id: int) -> None:
    await db.execute(delete(TimeSlot).where(TimeSlot.id == slot_id))
    await db.commit()