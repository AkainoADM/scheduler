from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.reference import Lesson
from app.schemas.lesson import LessonCreate, LessonUpdate
from typing import List

async def get_all_lessons(db: AsyncSession):
    result = await db.execute(select(Lesson).order_by(Lesson.date, Lesson.time_slot_id))
    return result.scalars().all()

async def get_lesson(db: AsyncSession, lesson_id: int):
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    return result.scalar_one_or_none()

async def create_lesson(db: AsyncSession, data: LessonCreate) -> Lesson:
    lesson = Lesson(**data.model_dump())
    # Вычисляем день недели автоматически
    lesson.week_day = data.date.isoweekday()
    db.add(lesson)
    await db.commit()
    await db.refresh(lesson)
    return lesson

async def update_lesson(db: AsyncSession, lesson_id: int, data: LessonUpdate) -> Lesson | None:
    values = data.model_dump(exclude_unset=True)
    if "date" in values and values["date"]:
        values["week_day"] = values["date"].isoweekday()
    stmt = update(Lesson).where(Lesson.id == lesson_id).values(**values).returning(Lesson)
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one_or_none()

async def delete_lesson(db: AsyncSession, lesson_id: int) -> None:
    await db.execute(delete(Lesson).where(Lesson.id == lesson_id))
    await db.commit()

async def bulk_delete_lessons(db: AsyncSession, ids: List[int]) -> None:
    await db.execute(delete(Lesson).where(Lesson.id.in_(ids)))
    await db.commit()