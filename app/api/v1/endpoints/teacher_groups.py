from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.services import teacher_group as service
from pydantic import BaseModel

router = APIRouter(prefix="/teacher-groups", tags=["Teacher Groups"])

class TeacherGroupCreate(BaseModel):
    teacher_id: int
    group_id: int

class TeacherGroupResponse(BaseModel):
    teacher_id: int
    group_id: int

@router.get("/", response_model=List[TeacherGroupResponse])
async def read_all(db: AsyncSession = Depends(get_db)):
    items = await service.get_all_teacher_groups(db)
    return [{"teacher_id": row.teachers_id, "group_id": row.groups_id} for row in items]

@router.post("/", response_model=TeacherGroupResponse)
async def create(data: TeacherGroupCreate, db: AsyncSession = Depends(get_db)):
    item = await service.create_teacher_group(db, data.teacher_id, data.group_id)
    if not item:
        raise HTTPException(status_code=400, detail="Связь уже существует")
    return item

@router.delete("/{teacher_id}/{group_id}")
async def delete(teacher_id: int, group_id: int, db: AsyncSession = Depends(get_db)):
    await service.delete_teacher_group(db, teacher_id, group_id)
    return {"ok": True}

@router.post("/bulk-delete")
async def bulk_delete(ids: List[List[int]], db: AsyncSession = Depends(get_db)):
    await service.bulk_delete_teacher_groups(db, [(i[0], i[1]) for i in ids])
    return {"ok": True}