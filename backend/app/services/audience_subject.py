from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, insert
from app.models.reference import op_audiences_of_pairs

async def get_all_audience_subjects(db: AsyncSession):
    result = await db.execute(select(op_audiences_of_pairs))
    rows = result.all()
    # Преобразуем строки в словари
    return [{"audience_id": row.audience_id, "subject_id": row.subject_id} for row in rows]

async def create_audience_subject(db: AsyncSession, audience_id: int, subject_id: int):
    existing = await db.execute(
        select(op_audiences_of_pairs).where(
            op_audiences_of_pairs.c.audience_id == audience_id,
            op_audiences_of_pairs.c.subject_id == subject_id
        )
    )
    if existing.first():
        return None
    stmt = insert(op_audiences_of_pairs).values(audience_id=audience_id, subject_id=subject_id)
    await db.execute(stmt)
    await db.commit()
    return {"audience_id": audience_id, "subject_id": subject_id}

async def delete_audience_subject(db: AsyncSession, audience_id: int, subject_id: int):
    await db.execute(
        delete(op_audiences_of_pairs).where(
            op_audiences_of_pairs.c.audience_id == audience_id,
            op_audiences_of_pairs.c.subject_id == subject_id
        )
    )
    await db.commit()

async def bulk_delete_audience_subjects(db: AsyncSession, pairs):
    for audience_id, subject_id in pairs:
        await db.execute(
            delete(op_audiences_of_pairs).where(
                op_audiences_of_pairs.c.audience_id == audience_id,
                op_audiences_of_pairs.c.subject_id == subject_id
            )
        )
    await db.commit()