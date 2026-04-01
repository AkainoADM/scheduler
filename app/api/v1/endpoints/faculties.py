from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import faculty as faculty_service
from app.schemas.faculty import FacultyCreate, FacultyResponse, FacultyUpdate
from typing import List

router = APIRouter(prefix="/faculties", tags=["Faculties"])

@router.get("/", response_model=list[FacultyResponse])
async def read_faculties(db: AsyncSession = Depends(get_db)):
    return await faculty_service.get_all_faculties(db)

@router.get("/{faculty_id}", response_model=FacultyResponse)
async def read_faculty(faculty_id: int, db: AsyncSession = Depends(get_db)):
    faculty = await faculty_service.get_faculty(db, faculty_id)
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty not found")
    return faculty

@router.post("/", response_model=FacultyResponse)
async def create_faculty(data: FacultyCreate, db: AsyncSession = Depends(get_db)):
    return await faculty_service.create_faculty(db, data)

@router.put("/{faculty_id}", response_model=FacultyResponse)
async def update_faculty(faculty_id: int, data: FacultyUpdate, db: AsyncSession = Depends(get_db)):
    faculty = await faculty_service.update_faculty(db, faculty_id, data)
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty not found")
    return faculty

@router.delete("/{faculty_id}")
async def delete_faculty(faculty_id: int, db: AsyncSession = Depends(get_db)):
    await faculty_service.delete_faculty(db, faculty_id)
    return {"ok": True}

@router.post("/bulk-delete")
async def bulk_delete_faculties(ids: List[int], db: AsyncSession = Depends(get_db)):
    await faculty_service.bulk_delete_faculties(db, ids)
    return {"ok": True}