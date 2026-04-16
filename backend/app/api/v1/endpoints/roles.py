from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import role as service
from app.schemas.role import RoleCreate, RoleResponse, RoleUpdate
from typing import List

router = APIRouter(prefix="/roles", tags=["Roles"])

@router.get("/", response_model=list[RoleResponse])
async def read_roles(db: AsyncSession = Depends(get_db)):
    return await service.get_all_roles(db)

@router.get("/{role_id}", response_model=RoleResponse)
async def read_role(role_id: int, db: AsyncSession = Depends(get_db)):
    role = await service.get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role

@router.post("/", response_model=RoleResponse)
async def create_role(data: RoleCreate, db: AsyncSession = Depends(get_db)):
    return await service.create_role(db, data)

@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(role_id: int, data: RoleUpdate, db: AsyncSession = Depends(get_db)):
    role = await service.update_role(db, role_id, data)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role

@router.delete("/{role_id}")
async def delete_role(role_id: int, db: AsyncSession = Depends(get_db)):
    await service.delete_role(db, role_id)
    return {"ok": True}

@router.post("/bulk-delete")
async def bulk_delete_roles(ids: List[int], db: AsyncSession = Depends(get_db)):
    await service.bulk_delete_roles(db, ids)
    return {"ok": True}

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.services import role as role_service
from app.services import excel_import
from app.schemas.role import RoleCreate, RoleResponse, RoleUpdate

router = APIRouter(prefix="/roles", tags=["Roles"])

@router.get("/", response_model=List[RoleResponse])
async def read_roles(db: AsyncSession = Depends(get_db)):
    return await role_service.get_all_roles(db)

@router.get("/{role_id}", response_model=RoleResponse)
async def read_role(role_id: int, db: AsyncSession = Depends(get_db)):
    role = await role_service.get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role

@router.post("/", response_model=RoleResponse)
async def create_role(data: RoleCreate, db: AsyncSession = Depends(get_db)):
    return await role_service.create_role(db, data)

@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(role_id: int, data: RoleUpdate, db: AsyncSession = Depends(get_db)):
    role = await role_service.update_role(db, role_id, data)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role

@router.delete("/{role_id}")
async def delete_role(role_id: int, db: AsyncSession = Depends(get_db)):
    await role_service.delete_role(db, role_id)
    return {"ok": True}

@router.post("/bulk-delete")
async def bulk_delete_roles(ids: List[int], db: AsyncSession = Depends(get_db)):
    await role_service.bulk_delete_roles(db, ids)
    return {"ok": True}

@router.post("/upload", summary="Загрузить роли из Excel")
async def upload_roles(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "Файл должен быть Excel (.xlsx или .xls)")
    try:
        content = await file.read()
        rows = await excel_import.parse_roles_excel(content)
    except Exception as e:
        raise HTTPException(400, f"Ошибка чтения файла: {str(e)}")
    valid, errors = await excel_import.validate_roles_data(rows, db)
    result = await excel_import.save_roles_from_validated(valid, db)
    return {
        "message": "Загрузка завершена",
        "added": result["added"],
        "updated": result["updated"],
        "errors": errors
    }