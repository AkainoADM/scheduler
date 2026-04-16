from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.services import template_item as service
from app.schemas.template_item import TemplateItemCreate, TemplateItemResponse, TemplateItemUpdate

router = APIRouter(prefix="/template-items", tags=["Template Items"])

@router.get("/", response_model=List[TemplateItemResponse])
async def read_items(db: AsyncSession = Depends(get_db)):
    return await service.get_all_template_items(db)

@router.get("/{item_id}", response_model=TemplateItemResponse)
async def read_item(item_id: int, db: AsyncSession = Depends(get_db)):
    item = await service.get_template_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.post("/", response_model=TemplateItemResponse)
async def create_item(data: TemplateItemCreate, db: AsyncSession = Depends(get_db)):
    return await service.create_template_item(db, data)

@router.put("/{item_id}", response_model=TemplateItemResponse)
async def update_item(item_id: int, data: TemplateItemUpdate, db: AsyncSession = Depends(get_db)):
    item = await service.update_template_item(db, item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.delete("/{item_id}")
async def delete_item(item_id: int, db: AsyncSession = Depends(get_db)):
    await service.delete_template_item(db, item_id)
    return {"ok": True}

@router.post("/bulk-delete")
async def bulk_delete_items(ids: List[int], db: AsyncSession = Depends(get_db)):
    await service.bulk_delete_template_items(db, ids)
    return {"ok": True}