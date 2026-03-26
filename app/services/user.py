from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.reference import User
from app.schemas.user import UserCreate, UserUpdate

async def get_all_users(db: AsyncSession):
    result = await db.execute(select(User))
    return result.scalars().all()

async def get_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, data: UserCreate) -> User:
    # Пока не хешируем пароль, просто сохраняем как есть. Если нужно, можно добавить хеширование.
    user = User(**data.model_dump())
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def update_user(db: AsyncSession, user_id: int, data: UserUpdate) -> User | None:
    stmt = update(User).where(User.id == user_id).values(**data.model_dump(exclude_unset=True)).returning(User)
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one_or_none()

async def delete_user(db: AsyncSession, user_id: int) -> None:
    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()