from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.database import engine, get_db
from app.services.scheduler import generate_schedule as sync_generate
from app.models.schedule import ScheduleItem, FinalScheduleItem, Lesson, Subject
from app.models.reference import Audience, TimeSlot
from sqlalchemy import select, delete
from typing import List
import asyncio

router = APIRouter(prefix="/generator", tags=["Generator"])

# Функция для запуска синхронного генератора в отдельном потоке
async def run_generator(db_session):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, sync_generate, db_session)
    return result

@router.post("/generate")
async def generate(db: AsyncSession = Depends(get_db)):
    # Создаём синхронную сессию на основе того же движка
    sync_session = sessionmaker(engine, expire_on_commit=False)()
    try:
        result = await run_generator(sync_session)
        return result
    finally:
        sync_session.close()

@router.get("/schedule")
async def get_schedule(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScheduleItem))
    items = result.scalars().all()
    schedule_data = []
    for item in items:
        lesson = await db.get(Lesson, item.lesson_id)
        subject = await db.get(Subject, lesson.subject_id) if lesson else None
        teacher_name = "Не назначен"
        if subject and subject.teachers:
            teacher_name = ", ".join([t.name for t in subject.teachers])
        schedule_data.append({
            "subject": subject.name if subject else "---",
            "teacher": teacher_name,
            "audience": item.audience.name if item.audience else "---",
            "date": str(item.date),
            "pair": item.time_slot.slot_number if item.time_slot else None,
            "time": f"{item.time_slot.start_time} - {item.time_slot.end_time}" if item.time_slot else "---",
            "id": item.id,
            "is_pinned": item.is_pinned
        })
    return schedule_data

@router.post("/schedule/pin/{item_id}")
async def pin_item(item_id: int, db: AsyncSession = Depends(get_db)):
    item = await db.get(ScheduleItem, item_id)
    if not item:
        raise HTTPException(404, "Запись не найдена")
    item.is_pinned = not item.is_pinned
    await db.commit()
    return {"is_pinned": item.is_pinned}

@router.post("/schedule/approve")
async def approve_schedule(db: AsyncSession = Depends(get_db)):
    await db.execute(delete(FinalScheduleItem))
    result = await db.execute(select(ScheduleItem))
    drafts = result.scalars().all()
    for d in drafts:
        final = FinalScheduleItem(
            lesson_id=d.lesson_id,
            time_slot_id=d.time_slot_id,
            audience_id=d.audience_id,
            date=d.date
        )
        db.add(final)
    await db.commit()
    return {"status": "success"}