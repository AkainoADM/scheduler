from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.reference import DayOfWeek
from app.schemas.day_of_week import DayOfWeekCreate, DayOfWeekUpdate
from typing import List

async def get_all_days_of_week(db: AsyncSession):
    result = await db.execute(select(DayOfWeek).order_by(DayOfWeek.id))
    return result.scalars().all()

async def get_day_of_week(db: AsyncSession, dow_id: int):
    result = await db.execute(select(DayOfWeek).where(DayOfWeek.id == dow_id))
    return result.scalar_one_or_none()

async def create_day_of_week(db: AsyncSession, data: DayOfWeekCreate) -> DayOfWeek:
    dow = DayOfWeek(**data.model_dump())
    db.add(dow)
    await db.commit()
    await db.refresh(dow)
    return dow

async def update_day_of_week(db: AsyncSession, dow_id: int, data: DayOfWeekUpdate) -> DayOfWeek | None:
    stmt = update(DayOfWeek).where(DayOfWeek.id == dow_id).values(**data.model_dump(exclude_unset=True)).returning(DayOfWeek)
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one_or_none()

async def delete_day_of_week(db: AsyncSession, dow_id: int) -> None:
    await db.execute(delete(DayOfWeek).where(DayOfWeek.id == dow_id))
    await db.commit()

async def bulk_delete_days_of_week(db: AsyncSession, ids: List[int]) -> None:
    await db.execute(delete(DayOfWeek).where(DayOfWeek.id.in_(ids)))
    await db.commit()