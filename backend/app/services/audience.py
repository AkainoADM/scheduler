from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.reference import Audience
from app.schemas.audience import AudienceCreate, AudienceUpdate
from typing import List

async def get_all_audiences(db: AsyncSession):
    result = await db.execute(select(Audience).order_by(Audience.id))
    return result.scalars().all()

async def get_audience(db: AsyncSession, audience_id: int):
    result = await db.execute(select(Audience).where(Audience.id == audience_id))
    return result.scalar_one_or_none()

async def create_audience(db: AsyncSession, data: AudienceCreate) -> Audience:
    audience = Audience(**data.model_dump())
    db.add(audience)
    await db.commit()
    await db.refresh(audience)
    return audience

async def update_audience(db: AsyncSession, audience_id: int, data: AudienceUpdate) -> Audience | None:
    stmt = update(Audience).where(Audience.id == audience_id).values(**data.model_dump(exclude_unset=True)).returning(Audience)
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one_or_none()

async def delete_audience(db: AsyncSession, audience_id: int) -> None:
    await db.execute(delete(Audience).where(Audience.id == audience_id))
    await db.commit()

async def bulk_delete_audiences(db: AsyncSession, ids: List[int]) -> None:
    await db.execute(delete(Audience).where(Audience.id.in_(ids)))
    await db.commit()