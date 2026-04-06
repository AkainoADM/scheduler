from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, insert
from app.models.reference import op_teachers_groups

async def get_all_teacher_groups(db: AsyncSession):
    result = await db.execute(select(op_teachers_groups))
    rows = result.all()
    # Используем правильные имена колонок: teachers_id, groups_id
    return [{"teacher_id": row._mapping['teachers_id'], "group_id": row._mapping['groups_id']} for row in rows]

async def create_teacher_group(db: AsyncSession, teacher_id: int, group_id: int):
    existing = await db.execute(
        select(op_teachers_groups).where(
            op_teachers_groups.c.teachers_id == teacher_id,
            op_teachers_groups.c.groups_id == group_id
        )
    )
    if existing.first():
        return None
    stmt = insert(op_teachers_groups).values(teachers_id=teacher_id, groups_id=group_id)
    await db.execute(stmt)
    await db.commit()
    return {"teacher_id": teacher_id, "group_id": group_id}

async def delete_teacher_group(db: AsyncSession, teacher_id: int, group_id: int):
    await db.execute(
        delete(op_teachers_groups).where(
            op_teachers_groups.c.teachers_id == teacher_id,
            op_teachers_groups.c.groups_id == group_id
        )
    )
    await db.commit()

async def bulk_delete_teacher_groups(db: AsyncSession, pairs):
    for teacher_id, group_id in pairs:
        await db.execute(
            delete(op_teachers_groups).where(
                op_teachers_groups.c.teachers_id == teacher_id,
                op_teachers_groups.c.groups_id == group_id
            )
        )
    await db.commit()