from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.reference import UserType
from app.schemas.user_type import UserTypeCreate, UserTypeUpdate
from typing import List

async def get_all_user_types(db: AsyncSession):
    result = await db.execute(select(UserType).order_by(UserType.id))
    return result.scalars().all()

async def get_user_type(db: AsyncSession, ut_id: int):
    result = await db.execute(select(UserType).where(UserType.id == ut_id))
    return result.scalar_one_or_none()

async def create_user_type(db: AsyncSession, data: UserTypeCreate) -> UserType:
    ut = UserType(**data.model_dump())
    db.add(ut)
    await db.commit()
    await db.refresh(ut)
    return ut

async def update_user_type(db: AsyncSession, ut_id: int, data: UserTypeUpdate) -> UserType | None:
    stmt = update(UserType).where(UserType.id == ut_id).values(**data.model_dump(exclude_unset=True)).returning(UserType)
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one_or_none()

async def delete_user_type(db: AsyncSession, ut_id: int) -> None:
    await db.execute(delete(UserType).where(UserType.id == ut_id))
    await db.commit()

async def bulk_delete_user_types(db: AsyncSession, ids: List[int]) -> None:
    await db.execute(delete(UserType).where(UserType.id.in_(ids)))
    await db.commit()