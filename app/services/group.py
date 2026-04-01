from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.reference import Group
from app.schemas.group import GroupCreate, GroupUpdate
from typing import List
from sqlalchemy import select, update, delete
from app.models.reference import Group
from app.schemas.group import GroupCreate, GroupUpdate

# ... остальные функции
async def bulk_delete_groups(db: AsyncSession, ids: List[int]) -> None:
    await db.execute(delete(Group).where(Group.id.in_(ids)))
    await db.commit()

async def get_all_groups(db: AsyncSession):
    result = await db.execute(select(Group))
    return result.scalars().all()

async def get_group(db: AsyncSession, group_id: int):
    result = await db.execute(select(Group).where(Group.id == group_id))
    return result.scalar_one_or_none()

async def create_group(db: AsyncSession, data: GroupCreate) -> Group:
    group = Group(**data.model_dump())
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group

async def update_group(db: AsyncSession, group_id: int, data: GroupUpdate) -> Group | None:
    stmt = update(Group).where(Group.id == group_id).values(**data.model_dump(exclude_unset=True)).returning(Group)
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one_or_none()

async def delete_group(db: AsyncSession, group_id: int) -> None:
    await db.execute(delete(Group).where(Group.id == group_id))
    await db.commit()

from sqlalchemy import delete

async def bulk_delete_groups(db: AsyncSession, ids: List[int]) -> None:
    await db.execute(delete(Group).where(Group.id.in_(ids)))
    await db.commit()