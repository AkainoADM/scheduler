from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.reference import Calendar
from app.schemas.calendar import CalendarCreate, CalendarUpdate
from typing import List
from sqlalchemy import select, update, delete
from app.models.reference import Calendar
from app.schemas.calendar import CalendarCreate, CalendarUpdate

# ... функции
async def bulk_delete_calendar(db: AsyncSession, ids: List[int]) -> None:
    await db.execute(delete(Calendar).where(Calendar.id.in_(ids)))
    await db.commit()
    
async def get_all_calendar(db: AsyncSession):
    result = await db.execute(select(Calendar).order_by(Calendar.date))
    return result.scalars().all()

async def get_calendar_entry(db: AsyncSession, entry_id: int):
    result = await db.execute(select(Calendar).where(Calendar.id == entry_id))
    return result.scalar_one_or_none()

async def create_calendar_entry(db: AsyncSession, data: CalendarCreate) -> Calendar:
    entry = Calendar(**data.model_dump())
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry

async def update_calendar_entry(db: AsyncSession, entry_id: int, data: CalendarUpdate) -> Calendar | None:
    stmt = update(Calendar).where(Calendar.id == entry_id).values(**data.model_dump(exclude_unset=True)).returning(Calendar)
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one_or_none()

async def delete_calendar_entry(db: AsyncSession, entry_id: int) -> None:
    await db.execute(delete(Calendar).where(Calendar.id == entry_id))
    await db.commit()

async def bulk_delete_calendar(db: AsyncSession, ids: List[int]) -> None:
    await db.execute(delete(Calendar).where(Calendar.id.in_(ids)))
    await db.commit()