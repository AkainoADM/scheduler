from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import subdivision as sub_service
from app.schemas.subdivision import SubdivisionCreate, SubdivisionResponse, SubdivisionUpdate
from typing import List

router = APIRouter(prefix="/subdivisions", tags=["Subdivisions"])

@router.get("/", response_model=list[SubdivisionResponse])
async def read_subdivisions(db: AsyncSession = Depends(get_db)):
    return await sub_service.get_all_subdivisions(db)

@router.get("/{sub_id}", response_model=SubdivisionResponse)
async def read_subdivision(sub_id: int, db: AsyncSession = Depends(get_db)):
    sub = await sub_service.get_subdivision(db, sub_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subdivision not found")
    return sub

@router.post("/", response_model=SubdivisionResponse)
async def create_subdivision(data: SubdivisionCreate, db: AsyncSession = Depends(get_db)):
    return await sub_service.create_subdivision(db, data)

@router.put("/{sub_id}", response_model=SubdivisionResponse)
async def update_subdivision(sub_id: int, data: SubdivisionUpdate, db: AsyncSession = Depends(get_db)):
    sub = await sub_service.update_subdivision(db, sub_id, data)
    if not sub:
        raise HTTPException(status_code=404, detail="Subdivision not found")
    return sub

@router.delete("/{sub_id}")
async def delete_subdivision(sub_id: int, db: AsyncSession = Depends(get_db)):
    await sub_service.delete_subdivision(db, sub_id)
    return {"ok": True}

@router.post("/bulk-delete")
async def bulk_delete_subdivisions(ids: List[int], db: AsyncSession = Depends(get_db)):
    await sub_service.bulk_delete_subdivisions(db, ids)
    return {"ok": True}