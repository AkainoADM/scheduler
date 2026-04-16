from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import subdivision as service
from app.schemas.subdivision import SubdivisionCreate, SubdivisionResponse, SubdivisionUpdate
from typing import List

router = APIRouter(prefix="/subdivisions", tags=["Subdivisions"])


@router.get("/{sub_id}", response_model=SubdivisionResponse)
async def read_subdivision(sub_id: int, db: AsyncSession = Depends(get_db)):
    sub = await service.get_subdivision(db, sub_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subdivision not found")
    return sub

@router.put("/{sub_id}", response_model=SubdivisionResponse)
async def update_subdivision(sub_id: int, data: SubdivisionUpdate, db: AsyncSession = Depends(get_db)):
    sub = await service.update_subdivision(db, sub_id, data)
    if not sub:
        raise HTTPException(status_code=404, detail="Subdivision not found")
    return sub

@router.delete("/{sub_id}")
async def delete_subdivision(sub_id: int, db: AsyncSession = Depends(get_db)):
    await service.delete_subdivision(db, sub_id)
    return {"ok": True}

@router.post("/bulk-delete")
async def bulk_delete_subdivisions(ids: List[int], db: AsyncSession = Depends(get_db)):
    await service.bulk_delete_subdivisions(db, ids)
    return {"ok": True}

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.services import subdivision as subdivision_service
from app.services import excel_import
from app.schemas.subdivision import SubdivisionCreate, SubdivisionResponse, SubdivisionUpdate

router = APIRouter(prefix="/subdivisions", tags=["Subdivisions"])

@router.get("/", response_model=List[SubdivisionResponse])
async def read_subdivisions(db: AsyncSession = Depends(get_db)):
    return await subdivision_service.get_all_subdivisions(db)

@router.get("/{sub_id}", response_model=SubdivisionResponse)
async def read_subdivision(sub_id: int, db: AsyncSession = Depends(get_db)):
    sub = await subdivision_service.get_subdivision(db, sub_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subdivision not found")
    return sub

@router.post("/", response_model=SubdivisionResponse)
async def create_subdivision(data: SubdivisionCreate, db: AsyncSession = Depends(get_db)):
    return await subdivision_service.create_subdivision(db, data)

@router.put("/{sub_id}", response_model=SubdivisionResponse)
async def update_subdivision(sub_id: int, data: SubdivisionUpdate, db: AsyncSession = Depends(get_db)):
    sub = await subdivision_service.update_subdivision(db, sub_id, data)
    if not sub:
        raise HTTPException(status_code=404, detail="Subdivision not found")
    return sub

@router.delete("/{sub_id}")
async def delete_subdivision(sub_id: int, db: AsyncSession = Depends(get_db)):
    await subdivision_service.delete_subdivision(db, sub_id)
    return {"ok": True}

@router.post("/bulk-delete")
async def bulk_delete_subdivisions(ids: List[int], db: AsyncSession = Depends(get_db)):
    await subdivision_service.bulk_delete_subdivisions(db, ids)
    return {"ok": True}

@router.post("/upload", summary="Загрузить подразделения из Excel")
async def upload_subdivisions(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "Файл должен быть Excel (.xlsx или .xls)")
    try:
        content = await file.read()
        rows = await excel_import.parse_subdivisions_excel(content)
    except Exception as e:
        raise HTTPException(400, f"Ошибка чтения файла: {str(e)}")
    valid, errors = await excel_import.validate_subdivisions_data(rows, db)
    result = await excel_import.save_subdivisions_from_validated(valid, db)
    return {
        "message": "Загрузка завершена",
        "added": result["added"],
        "updated": result["updated"],
        "errors": errors
    }