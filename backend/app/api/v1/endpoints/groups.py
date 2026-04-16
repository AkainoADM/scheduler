from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import group as service
from app.schemas.group import GroupCreate, GroupResponse, GroupUpdate
from typing import List

router = APIRouter(prefix="/groups", tags=["Groups"])

@router.get("/", response_model=list[GroupResponse])
async def read_groups(db: AsyncSession = Depends(get_db)):
    return await service.get_all_groups(db)

@router.get("/{group_id}", response_model=GroupResponse)
async def read_group(group_id: int, db: AsyncSession = Depends(get_db)):
    group = await service.get_group(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group

@router.post("/", response_model=GroupResponse)
async def create_group(data: GroupCreate, db: AsyncSession = Depends(get_db)):
    return await service.create_group(db, data)

@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(group_id: int, data: GroupUpdate, db: AsyncSession = Depends(get_db)):
    group = await service.update_group(db, group_id, data)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group

@router.delete("/{group_id}")
async def delete_group(group_id: int, db: AsyncSession = Depends(get_db)):
    await service.delete_group(db, group_id)
    return {"ok": True}

@router.post("/bulk-delete")
async def bulk_delete_groups(ids: List[int], db: AsyncSession = Depends(get_db)):
    await service.bulk_delete_groups(db, ids)
    return {"ok": True}

from fastapi import UploadFile, File, HTTPException
from app.services import excel_import

@router.post("/upload", summary="Загрузить группы из Excel")
async def upload_groups(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "Файл должен быть Excel (.xlsx или .xls)")
    try:
        content = await file.read()
        rows = await excel_import.parse_groups_excel(content)
    except Exception as e:
        raise HTTPException(400, f"Ошибка чтения файла: {str(e)}")
    valid, errors = await excel_import.validate_groups_data(rows, db)
    result = await excel_import.save_groups_from_validated(valid, db)
    return {
        "message": "Загрузка завершена",
        "added": result["added"],
        "updated": result["updated"],
        "errors": errors
    }