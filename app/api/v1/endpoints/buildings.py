from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import building as service
from app.schemas.building import BuildingCreate, BuildingResponse, BuildingUpdate
from typing import List

from fastapi import UploadFile, File
from app.services import excel_import

router = APIRouter(prefix="/buildings", tags=["Buildings"])

@router.get("/", response_model=list[BuildingResponse])
async def read_buildings(db: AsyncSession = Depends(get_db)):
    return await service.get_all_buildings(db)

@router.get("/{building_id}", response_model=BuildingResponse)
async def read_building(building_id: int, db: AsyncSession = Depends(get_db)):
    building = await service.get_building(db, building_id)
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    return building

@router.post("/", response_model=BuildingResponse)
async def create_building(data: BuildingCreate, db: AsyncSession = Depends(get_db)):
    return await service.create_building(db, data)

@router.put("/{building_id}", response_model=BuildingResponse)
async def update_building(building_id: int, data: BuildingUpdate, db: AsyncSession = Depends(get_db)):
    building = await service.update_building(db, building_id, data)
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    return building

@router.delete("/{building_id}")
async def delete_building(building_id: int, db: AsyncSession = Depends(get_db)):
    await service.delete_building(db, building_id)
    return {"ok": True}

@router.post("/bulk-delete")
async def bulk_delete_buildings(ids: List[int], db: AsyncSession = Depends(get_db)):
    await service.bulk_delete_buildings(db, ids)
    return {"ok": True}

@router.post("/upload", summary="Загрузить здания из Excel")
async def upload_buildings(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "Файл должен быть Excel (.xlsx или .xls)")
    try:
        content = await file.read()
        rows = await excel_import.parse_buildings_excel(content)
    except Exception as e:
        raise HTTPException(400, f"Ошибка чтения файла: {str(e)}")
    valid, errors = await excel_import.validate_buildings_data(rows, db)
    result = await excel_import.save_buildings_from_validated(valid, db)
    return {
        "message": "Загрузка завершена",
        "added": result["added"],
        "updated": result["updated"],
        "errors": errors
    }