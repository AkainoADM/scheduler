from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.services import audience_subject as service
from pydantic import BaseModel

router = APIRouter(prefix="/audience-subjects", tags=["Audience Subjects"])

class AudienceSubjectCreate(BaseModel):
    audience_id: int
    subject_id: int

class AudienceSubjectResponse(BaseModel):
    audience_id: int
    subject_id: int

@router.get("/", response_model=List[AudienceSubjectResponse])
async def read_all(db: AsyncSession = Depends(get_db)):
    items = await service.get_all_audience_subjects(db)
    return [{"audience_id": row.audience_id, "subject_id": row.subject_id} for row in items]

@router.post("/", response_model=AudienceSubjectResponse)
async def create(data: AudienceSubjectCreate, db: AsyncSession = Depends(get_db)):
    item = await service.create_audience_subject(db, data.audience_id, data.subject_id)
    if not item:
        raise HTTPException(status_code=400, detail="Связь уже существует")
    return item

@router.delete("/{audience_id}/{subject_id}")
async def delete(audience_id: int, subject_id: int, db: AsyncSession = Depends(get_db)):
    await service.delete_audience_subject(db, audience_id, subject_id)
    return {"ok": True}

@router.post("/bulk-delete")
async def bulk_delete(ids: List[List[int]], db: AsyncSession = Depends(get_db)):
    await service.bulk_delete_audience_subjects(db, [(i[0], i[1]) for i in ids])
    return {"ok": True}