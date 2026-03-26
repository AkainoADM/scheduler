from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.reference import Permission
from app.schemas.permission import PermissionCreate, PermissionUpdate

async def get_all_permissions(db: AsyncSession):
    result = await db.execute(select(Permission))
    return result.scalars().all()

async def get_permission(db: AsyncSession, perm_id: int):
    result = await db.execute(select(Permission).where(Permission.id == perm_id))
    return result.scalar_one_or_none()

async def create_permission(db: AsyncSession, data: PermissionCreate) -> Permission:
    perm = Permission(**data.model_dump())
    db.add(perm)
    await db.commit()
    await db.refresh(perm)
    return perm

async def update_permission(db: AsyncSession, perm_id: int, data: PermissionUpdate) -> Permission | None:
    stmt = update(Permission).where(Permission.id == perm_id).values(**data.model_dump(exclude_unset=True)).returning(Permission)
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one_or_none()

async def delete_permission(db: AsyncSession, perm_id: int) -> None:
    await db.execute(delete(Permission).where(Permission.id == perm_id))
    await db.commit()