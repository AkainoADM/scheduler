from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import audience as service
from app.schemas.audience import AudienceCreate, AudienceResponse, AudienceUpdate
from typing import List

from fastapi import UploadFile, File
from app.services import excel_import

router = APIRouter(prefix="/audiences", tags=["Audiences"])

@router.get("/", response_model=list[AudienceResponse])
async def read_audiences(db: AsyncSession = Depends(get_db)):
    return await service.get_all_audiences(db)

@router.get("/{audience_id}", response_model=AudienceResponse)
async def read_audience(audience_id: int, db: AsyncSession = Depends(get_db)):
    audience = await service.get_audience(db, audience_id)
    if not audience:
        raise HTTPException(status_code=404, detail="Audience not found")
    return audience

@router.post("/", response_model=AudienceResponse)
async def create_audience(data: AudienceCreate, db: AsyncSession = Depends(get_db)):
    return await service.create_audience(db, data)

@router.put("/{audience_id}", response_model=AudienceResponse)
async def update_audience(audience_id: int, data: AudienceUpdate, db: AsyncSession = Depends(get_db)):
    audience = await service.update_audience(db, audience_id, data)
    if not audience:
        raise HTTPException(status_code=404, detail="Audience not found")
    return audience

@router.delete("/{audience_id}")
async def delete_audience(audience_id: int, db: AsyncSession = Depends(get_db)):
    await service.delete_audience(db, audience_id)
    return {"ok": True}

@router.post("/bulk-delete")
async def bulk_delete_audiences(ids: List[int], db: AsyncSession = Depends(get_db)):
    await service.bulk_delete_audiences(db, ids)
    return {"ok": True}

@router.post("/upload", summary="Загрузить аудитории из Excel")
async def upload_audiences(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "Файл должен быть Excel (.xlsx или .xls)")
    try:
        content = await file.read()
        rows = await excel_import.parse_audiences_excel(content)
    except Exception as e:
        raise HTTPException(400, f"Ошибка чтения файла: {str(e)}")
    valid, errors = await excel_import.validate_audiences_data(rows, db)
    result = await excel_import.save_audiences_from_validated(valid, db)
    return {
        "message": "Загрузка завершена",
        "added": result["added"],
        "updated": result["updated"],
        "errors": errors
    }