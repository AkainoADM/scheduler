from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.services import template_name as service
from app.schemas.template_name import TemplateNameCreate, TemplateNameResponse, TemplateNameUpdate

router = APIRouter(prefix="/template-names", tags=["Template Names"])

@router.get("/", response_model=List[TemplateNameResponse])
async def read_all(db: AsyncSession = Depends(get_db)):
    return await service.get_all_template_names(db)

@router.get("/{item_id}", response_model=TemplateNameResponse)
async def read_one(item_id: int, db: AsyncSession = Depends(get_db)):
    item = await service.get_template_name(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Template name not found")
    return item

@router.post("/", response_model=TemplateNameResponse)
async def create(data: TemplateNameCreate, db: AsyncSession = Depends(get_db)):
    return await service.create_template_name(db, data)

@router.put("/{item_id}", response_model=TemplateNameResponse)
async def update(item_id: int, data: TemplateNameUpdate, db: AsyncSession = Depends(get_db)):
    item = await service.update_template_name(db, item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Template name not found")
    return item

@router.delete("/{item_id}")
async def delete(item_id: int, db: AsyncSession = Depends(get_db)):
    await service.delete_template_name(db, item_id)
    return {"ok": True}

@router.post("/bulk-delete")
async def bulk_delete(ids: List[int], db: AsyncSession = Depends(get_db)):
    await service.bulk_delete_template_names(db, ids)
    return {"ok": True}