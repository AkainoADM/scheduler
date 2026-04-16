from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.reference import Subject
from app.schemas.subject import SubjectCreate, SubjectUpdate
from typing import List

async def get_all_subjects(db: AsyncSession):
    result = await db.execute(select(Subject).order_by(Subject.id))
    return result.scalars().all()

async def get_subject(db: AsyncSession, subject_id: int):
    result = await db.execute(select(Subject).where(Subject.id == subject_id))
    return result.scalar_one_or_none()

async def create_subject(db: AsyncSession, data: SubjectCreate) -> Subject:
    subject = Subject(**data.model_dump())
    db.add(subject)
    await db.commit()
    await db.refresh(subject)
    return subject

async def update_subject(db: AsyncSession, subject_id: int, data: SubjectUpdate) -> Subject | None:
    stmt = update(Subject).where(Subject.id == subject_id).values(**data.model_dump(exclude_unset=True)).returning(Subject)
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one_or_none()

async def delete_subject(db: AsyncSession, subject_id: int) -> None:
    await db.execute(delete(Subject).where(Subject.id == subject_id))
    await db.commit()

async def bulk_delete_subjects(db: AsyncSession, ids: List[int]) -> None:
    await db.execute(delete(Subject).where(Subject.id.in_(ids)))
    await db.commit()