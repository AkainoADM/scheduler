from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, insert, update
from app.models.reference import op_teachers_of_pairs

async def get_all_teacher_subjects(db: AsyncSession):
    result = await db.execute(select(op_teachers_of_pairs))
    return result.all()

async def create_teacher_subject(db: AsyncSession, teacher_id: int, subject_id: int, is_main: bool = False):
    existing = await db.execute(
        select(op_teachers_of_pairs).where(
            op_teachers_of_pairs.c.teacher_id == teacher_id,
            op_teachers_of_pairs.c.subject_id == subject_id
        )
    )
    if existing.first():
        return None
    stmt = insert(op_teachers_of_pairs).values(teacher_id=teacher_id, subject_id=subject_id, is_main=is_main)
    await db.execute(stmt)
    await db.commit()
    return {"teacher_id": teacher_id, "subject_id": subject_id, "is_main": is_main}

async def update_teacher_subject(db: AsyncSession, teacher_id: int, subject_id: int, is_main: bool):
    stmt = update(op_teachers_of_pairs).where(
        op_teachers_of_pairs.c.teacher_id == teacher_id,
        op_teachers_of_pairs.c.subject_id == subject_id
    ).values(is_main=is_main)
    await db.execute(stmt)
    await db.commit()

async def delete_teacher_subject(db: AsyncSession, teacher_id: int, subject_id: int):
    await db.execute(
        delete(op_teachers_of_pairs).where(
            op_teachers_of_pairs.c.teacher_id == teacher_id,
            op_teachers_of_pairs.c.subject_id == subject_id
        )
    )
    await db.commit()

async def bulk_delete_teacher_subjects(db: AsyncSession, pairs):
    for teacher_id, subject_id in pairs:
        await db.execute(
            delete(op_teachers_of_pairs).where(
                op_teachers_of_pairs.c.teacher_id == teacher_id,
                op_teachers_of_pairs.c.subject_id == subject_id
            )
        )
    await db.commit()

async def get_all_teacher_subjects(db: AsyncSession):
    result = await db.execute(select(op_teachers_of_pairs))
    rows = result.all()
    return [{"teacher_id": row.teacher_id, "subject_id": row.subject_id, "is_main": row.is_main} for row in rows]