from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.services import teacher_subject as service
from pydantic import BaseModel

router = APIRouter(prefix="/teacher-subjects", tags=["Teacher Subjects"])

class TeacherSubjectCreate(BaseModel):
    teacher_id: int
    subject_id: int
    is_main: bool = False

class TeacherSubjectResponse(BaseModel):
    teacher_id: int
    subject_id: int
    is_main: bool

class TeacherSubjectUpdate(BaseModel):
    is_main: bool

@router.get("/", response_model=List[TeacherSubjectResponse])
async def read_all(db: AsyncSession = Depends(get_db)):
    items = await service.get_all_teacher_subjects(db)
    return [{"teacher_id": row.teacher_id, "subject_id": row.subject_id, "is_main": row.is_main} for row in items]

@router.post("/", response_model=TeacherSubjectResponse)
async def create(data: TeacherSubjectCreate, db: AsyncSession = Depends(get_db)):
    item = await service.create_teacher_subject(db, data.teacher_id, data.subject_id, data.is_main)
    if not item:
        raise HTTPException(status_code=400, detail="Связь уже существует")
    return item

@router.put("/{teacher_id}/{subject_id}")
async def update(teacher_id: int, subject_id: int, data: TeacherSubjectUpdate, db: AsyncSession = Depends(get_db)):
    await service.update_teacher_subject(db, teacher_id, subject_id, data.is_main)
    return {"ok": True}

@router.delete("/{teacher_id}/{subject_id}")
async def delete(teacher_id: int, subject_id: int, db: AsyncSession = Depends(get_db)):
    await service.delete_teacher_subject(db, teacher_id, subject_id)
    return {"ok": True}

@router.post("/bulk-delete")
async def bulk_delete(ids: List[List[int]], db: AsyncSession = Depends(get_db)):
    await service.bulk_delete_teacher_subjects(db, [(i[0], i[1]) for i in ids])
    return {"ok": True}