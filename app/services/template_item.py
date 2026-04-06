from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.reference import TemplateItem
from app.schemas.template_item import TemplateItemCreate, TemplateItemUpdate
from typing import List

async def get_all_template_items(db: AsyncSession):
    result = await db.execute(select(TemplateItem).order_by(TemplateItem.id))
    return result.scalars().all()

async def get_template_item(db: AsyncSession, item_id: int):
    result = await db.execute(select(TemplateItem).where(TemplateItem.id == item_id))
    return result.scalar_one_or_none()

async def create_template_item(db: AsyncSession, data: TemplateItemCreate) -> TemplateItem:
    item = TemplateItem(**data.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item

async def update_template_item(db: AsyncSession, item_id: int, data: TemplateItemUpdate) -> TemplateItem | None:
    stmt = update(TemplateItem).where(TemplateItem.id == item_id).values(**data.model_dump(exclude_unset=True)).returning(TemplateItem)
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one_or_none()

async def delete_template_item(db: AsyncSession, item_id: int) -> None:
    await db.execute(delete(TemplateItem).where(TemplateItem.id == item_id))
    await db.commit()

async def bulk_delete_template_items(db: AsyncSession, ids: List[int]) -> None:
    await db.execute(delete(TemplateItem).where(TemplateItem.id.in_(ids)))
    await db.commit()