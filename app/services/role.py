from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.reference import Role
from app.schemas.role import RoleCreate, RoleUpdate
from typing import List

async def get_all_roles(db: AsyncSession):
    result = await db.execute(select(Role).order_by(Role.id))
    return result.scalars().all()

async def get_role(db: AsyncSession, role_id: int):
    result = await db.execute(select(Role).where(Role.id == role_id))
    return result.scalar_one_or_none()

async def create_role(db: AsyncSession, data: RoleCreate) -> Role:
    role = Role(**data.model_dump())
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role

async def update_role(db: AsyncSession, role_id: int, data: RoleUpdate) -> Role | None:
    stmt = update(Role).where(Role.id == role_id).values(**data.model_dump(exclude_unset=True)).returning(Role)
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one_or_none()

async def delete_role(db: AsyncSession, role_id: int) -> None:
    await db.execute(delete(Role).where(Role.id == role_id))
    await db.commit()

async def bulk_delete_roles(db: AsyncSession, ids: List[int]) -> None:
    await db.execute(delete(Role).where(Role.id.in_(ids)))
    await db.commit()