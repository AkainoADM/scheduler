from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import permission as service
from app.schemas.permission import PermissionCreate, PermissionResponse, PermissionUpdate
from typing import List

router = APIRouter(prefix="/permissions", tags=["Permissions"])

@router.get("/", response_model=list[PermissionResponse])
async def read_permissions(db: AsyncSession = Depends(get_db)):
    return await service.get_all_permissions(db)

@router.get("/{perm_id}", response_model=PermissionResponse)
async def read_permission(perm_id: int, db: AsyncSession = Depends(get_db)):
    perm = await service.get_permission(db, perm_id)
    if not perm:
        raise HTTPException(status_code=404, detail="Permission not found")
    return perm

@router.post("/", response_model=PermissionResponse)
async def create_permission(data: PermissionCreate, db: AsyncSession = Depends(get_db)):
    return await service.create_permission(db, data)

@router.put("/{perm_id}", response_model=PermissionResponse)
async def update_permission(perm_id: int, data: PermissionUpdate, db: AsyncSession = Depends(get_db)):
    perm = await service.update_permission(db, perm_id, data)
    if not perm:
        raise HTTPException(status_code=404, detail="Permission not found")
    return perm

@router.delete("/{perm_id}")
async def delete_permission(perm_id: int, db: AsyncSession = Depends(get_db)):
    await service.delete_permission(db, perm_id)
    return {"ok": True}

@router.post("/bulk-delete")
async def bulk_delete_permissions(ids: List[int], db: AsyncSession = Depends(get_db)):
    await service.bulk_delete_permissions(db, ids)
    return {"ok": True}

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.services import permission as permission_service
from app.services import excel_import
from app.schemas.permission import PermissionCreate, PermissionResponse, PermissionUpdate

router = APIRouter(prefix="/permissions", tags=["Permissions"])

@router.get("/", response_model=List[PermissionResponse])
async def read_permissions(db: AsyncSession = Depends(get_db)):
    return await permission_service.get_all_permissions(db)

@router.get("/{perm_id}", response_model=PermissionResponse)
async def read_permission(perm_id: int, db: AsyncSession = Depends(get_db)):
    perm = await permission_service.get_permission(db, perm_id)
    if not perm:
        raise HTTPException(status_code=404, detail="Permission not found")
    return perm

@router.post("/", response_model=PermissionResponse)
async def create_permission(data: PermissionCreate, db: AsyncSession = Depends(get_db)):
    return await permission_service.create_permission(db, data)

@router.put("/{perm_id}", response_model=PermissionResponse)
async def update_permission(perm_id: int, data: PermissionUpdate, db: AsyncSession = Depends(get_db)):
    perm = await permission_service.update_permission(db, perm_id, data)
    if not perm:
        raise HTTPException(status_code=404, detail="Permission not found")
    return perm

@router.delete("/{perm_id}")
async def delete_permission(perm_id: int, db: AsyncSession = Depends(get_db)):
    await permission_service.delete_permission(db, perm_id)
    return {"ok": True}

@router.post("/bulk-delete")
async def bulk_delete_permissions(ids: List[int], db: AsyncSession = Depends(get_db)):
    await permission_service.bulk_delete_permissions(db, ids)
    return {"ok": True}

@router.post("/upload", summary="Загрузить права из Excel")
async def upload_permissions(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "Файл должен быть Excel (.xlsx или .xls)")
    try:
        content = await file.read()
        rows = await excel_import.parse_permissions_excel(content)
    except Exception as e:
        raise HTTPException(400, f"Ошибка чтения файла: {str(e)}")
    valid, errors = await excel_import.validate_permissions_data(rows, db)
    result = await excel_import.save_permissions_from_validated(valid, db)
    return {
        "message": "Загрузка завершена",
        "added": result["added"],
        "updated": result["updated"],
        "errors": errors
    }