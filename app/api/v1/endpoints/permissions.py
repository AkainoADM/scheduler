from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import permission as permission_service
from app.schemas.permission import PermissionCreate, PermissionResponse, PermissionUpdate

router = APIRouter(prefix="/permissions", tags=["Permissions"])

@router.get("/", response_model=list[PermissionResponse])
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