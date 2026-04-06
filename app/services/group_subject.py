from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, insert
from app.models.reference import op_groups_of_pairs

async def get_all_group_subjects(db: AsyncSession):
    result = await db.execute(select(op_groups_of_pairs))
    rows = result.all()
    return [{"group_id": row.group_id, "subject_id": row.subject_id} for row in rows]

async def create_group_subject(db: AsyncSession, group_id: int, subject_id: int):
    existing = await db.execute(
        select(op_groups_of_pairs).where(
            op_groups_of_pairs.c.group_id == group_id,
            op_groups_of_pairs.c.subject_id == subject_id
        )
    )
    if existing.first():
        return None
    stmt = insert(op_groups_of_pairs).values(group_id=group_id, subject_id=subject_id)
    await db.execute(stmt)
    await db.commit()
    return {"group_id": group_id, "subject_id": subject_id}

async def delete_group_subject(db: AsyncSession, group_id: int, subject_id: int):
    await db.execute(
        delete(op_groups_of_pairs).where(
            op_groups_of_pairs.c.group_id == group_id,
            op_groups_of_pairs.c.subject_id == subject_id
        )
    )
    await db.commit()

async def bulk_delete_group_subjects(db: AsyncSession, pairs):
    for group_id, subject_id in pairs:
        await db.execute(
            delete(op_groups_of_pairs).where(
                op_groups_of_pairs.c.group_id == group_id,
                op_groups_of_pairs.c.subject_id == subject_id
            )
        )
    await db.commit()   