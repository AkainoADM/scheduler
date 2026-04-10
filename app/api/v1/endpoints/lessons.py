from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.services import lesson as lesson_service
from app.schemas.lesson import LessonCreate, LessonResponse, LessonUpdate

router = APIRouter(prefix="/lessons", tags=["Lessons"])

@router.get("/", response_model=List[LessonResponse])
async def read_lessons(db: AsyncSession = Depends(get_db)):
    return await lesson_service.get_all_lessons(db)

@router.get("/{lesson_id}", response_model=LessonResponse)
async def read_lesson(lesson_id: int, db: AsyncSession = Depends(get_db)):
    lesson = await lesson_service.get_lesson(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson

@router.post("/", response_model=LessonResponse)
async def create_lesson(data: LessonCreate, db: AsyncSession = Depends(get_db)):
    return await lesson_service.create_lesson(db, data)

@router.put("/{lesson_id}", response_model=LessonResponse)
async def update_lesson(lesson_id: int, data: LessonUpdate, db: AsyncSession = Depends(get_db)):
    lesson = await lesson_service.update_lesson(db, lesson_id, data)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson

@router.delete("/{lesson_id}")
async def delete_lesson(lesson_id: int, db: AsyncSession = Depends(get_db)):
    await lesson_service.delete_lesson(db, lesson_id)
    return {"ok": True}

@router.post("/bulk-delete")
async def bulk_delete_lessons(ids: List[int], db: AsyncSession = Depends(get_db)):
    await lesson_service.bulk_delete_lessons(db, ids)
    return {"ok": True}