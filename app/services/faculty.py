from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.reference import Faculty

async def get_all_faculties(db: AsyncSession):
    result = await db.execute(select(Faculty))
    return result.scalars().all()