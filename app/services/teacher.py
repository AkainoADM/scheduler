from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.reference import Teacher
from app.schemas.teacher import TeacherCreate, TeacherUpdate
from typing import List
from sqlalchemy import select, update, delete
from app.models.reference import Teacher
from app.schemas.teacher import TeacherCreate, TeacherUpdate

# ... функции
async def bulk_delete_teachers(db: AsyncSession, ids: List[int]) -> None:
    await db.execute(delete(Teacher).where(Teacher.id.in_(ids)))
    await db.commit()

async def get_all_teachers(db: AsyncSession):
    result = await db.execute(select(Teacher))
    return result.scalars().all()

async def get_teacher(db: AsyncSession, teacher_id: int):
    result = await db.execute(select(Teacher).where(Teacher.id == teacher_id))
    return result.scalar_one_or_none()

async def create_teacher(db: AsyncSession, data: TeacherCreate) -> Teacher:
    teacher = Teacher(**data.model_dump())
    db.add(teacher)
    await db.commit()
    await db.refresh(teacher)
    return teacher

async def update_teacher(db: AsyncSession, teacher_id: int, data: TeacherUpdate) -> Teacher | None:
    stmt = update(Teacher).where(Teacher.id == teacher_id).values(**data.model_dump(exclude_unset=True)).returning(Teacher)
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one_or_none()

async def delete_teacher(db: AsyncSession, teacher_id: int) -> None:
    await db.execute(delete(Teacher).where(Teacher.id == teacher_id))
    await db.commit()

async def bulk_delete_teachers(db: AsyncSession, ids: List[int]) -> None:
    await db.execute(delete(Teacher).where(Teacher.id.in_(ids)))
    await db.commit()