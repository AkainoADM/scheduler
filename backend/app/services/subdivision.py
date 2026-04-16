from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.reference import Subdivision
from app.schemas.subdivision import SubdivisionCreate, SubdivisionUpdate
from typing import List

async def get_all_subdivisions(db: AsyncSession):
    result = await db.execute(select(Subdivision).order_by(Subdivision.id))
    return result.scalars().all()

async def get_subdivision(db: AsyncSession, sub_id: int):
    result = await db.execute(select(Subdivision).where(Subdivision.id == sub_id))
    return result.scalar_one_or_none()

async def create_subdivision(db: AsyncSession, data: SubdivisionCreate) -> Subdivision:
    sub = Subdivision(**data.model_dump())
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub

async def update_subdivision(db: AsyncSession, sub_id: int, data: SubdivisionUpdate) -> Subdivision | None:
    stmt = update(Subdivision).where(Subdivision.id == sub_id).values(**data.model_dump(exclude_unset=True)).returning(Subdivision)
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one_or_none()

async def delete_subdivision(db: AsyncSession, sub_id: int) -> None:
    await db.execute(delete(Subdivision).where(Subdivision.id == sub_id))
    await db.commit()

async def bulk_delete_subdivisions(db: AsyncSession, ids: List[int]) -> None:
    await db.execute(delete(Subdivision).where(Subdivision.id.in_(ids)))
    await db.commit()