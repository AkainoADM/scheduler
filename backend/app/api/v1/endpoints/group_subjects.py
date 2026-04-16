from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.services import group_subject as service
from pydantic import BaseModel

router = APIRouter(prefix="/group-subjects", tags=["Group Subjects"])

class GroupSubjectCreate(BaseModel):
    group_id: int
    subject_id: int

class GroupSubjectResponse(BaseModel):
    group_id: int
    subject_id: int

@router.get("/", response_model=List[GroupSubjectResponse])
async def read_all(db: AsyncSession = Depends(get_db)):
    items = await service.get_all_group_subjects(db)
    return [{"group_id": row.group_id, "subject_id": row.subject_id} for row in items]

@router.post("/", response_model=GroupSubjectResponse)
async def create(data: GroupSubjectCreate, db: AsyncSession = Depends(get_db)):
    item = await service.create_group_subject(db, data.group_id, data.subject_id)
    if not item:
        raise HTTPException(status_code=400, detail="Связь уже существует")
    return item

@router.delete("/{group_id}/{subject_id}")
async def delete(group_id: int, subject_id: int, db: AsyncSession = Depends(get_db)):
    await service.delete_group_subject(db, group_id, subject_id)
    return {"ok": True}

@router.post("/bulk-delete")
async def bulk_delete(ids: List[List[int]], db: AsyncSession = Depends(get_db)):
    await service.bulk_delete_group_subjects(db, [(i[0], i[1]) for i in ids])
    return {"ok": True}