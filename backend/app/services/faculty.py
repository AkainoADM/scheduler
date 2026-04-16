from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.reference import Faculty
from app.schemas.faculty import FacultyCreate, FacultyUpdate
from typing import List

async def get_all_faculties(db: AsyncSession):
    result = await db.execute(select(Faculty).order_by(Faculty.id))
    return result.scalars().all()

async def get_faculty(db: AsyncSession, faculty_id: int):
    result = await db.execute(select(Faculty).where(Faculty.id == faculty_id))
    return result.scalar_one_or_none()

async def create_faculty(db: AsyncSession, data: FacultyCreate) -> Faculty:
    faculty = Faculty(**data.model_dump())
    db.add(faculty)
    await db.commit()
    await db.refresh(faculty)
    return faculty

async def update_faculty(db: AsyncSession, faculty_id: int, data: FacultyUpdate) -> Faculty | None:
    stmt = update(Faculty).where(Faculty.id == faculty_id).values(**data.model_dump(exclude_unset=True)).returning(Faculty)
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one_or_none()

async def delete_faculty(db: AsyncSession, faculty_id: int) -> None:
    await db.execute(delete(Faculty).where(Faculty.id == faculty_id))
    await db.commit()

async def bulk_delete_faculties(db: AsyncSession, ids: List[int]) -> None:
    await db.execute(delete(Faculty).where(Faculty.id.in_(ids)))
    await db.commit()