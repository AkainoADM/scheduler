from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import role as role_service
from app.schemas.role import RoleCreate, RoleResponse, RoleUpdate
from typing import List

router = APIRouter(prefix="/roles", tags=["Roles"])

@router.get("/", response_model=list[RoleResponse])
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