from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.reference import TemplateName
from app.schemas.template_name import TemplateNameCreate, TemplateNameUpdate
from typing import List

async def get_all_template_names(db: AsyncSession):
    result = await db.execute(select(TemplateName).order_by(TemplateName.id))
    return result.scalars().all()

async def get_template_name(db: AsyncSession, tn_id: int):
    result = await db.execute(select(TemplateName).where(TemplateName.id == tn_id))
    return result.scalar_one_or_none()

async def create_template_name(db: AsyncSession, data: TemplateNameCreate) -> TemplateName:
    tn = TemplateName(**data.model_dump())
    db.add(tn)
    await db.commit()
    await db.refresh(tn)
    return tn

async def update_template_name(db: AsyncSession, tn_id: int, data: TemplateNameUpdate) -> TemplateName | None:
    stmt = update(TemplateName).where(TemplateName.id == tn_id).values(**data.model_dump(exclude_unset=True)).returning(TemplateName)
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one_or_none()

async def delete_template_name(db: AsyncSession, tn_id: int) -> None:
    await db.execute(delete(TemplateName).where(TemplateName.id == tn_id))
    await db.commit()

async def bulk_delete_template_names(db: AsyncSession, ids: List[int]) -> None:
    await db.execute(delete(TemplateName).where(TemplateName.id.in_(ids)))
    await db.commit()