from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.scheduler import generate_schedule
from app.models.reference import ScheduleItem, FinalScheduleItem, Lesson, Subject, Audience, TimeSlot
from sqlalchemy.orm import selectinload
from sqlalchemy import select, delete

router = APIRouter(prefix="/generation", tags=["Generation"])

@router.post("/generate")
async def generate(db: AsyncSession = Depends(get_db)):
    result = await generate_schedule(db)
    if result["count"] == 0:
        return {"status": "error", "message": "Недостаточно данных"}
    return result

@router.get("/schedule")
async def get_schedule(db: AsyncSession = Depends(get_db)):
    items_result = await db.execute(
        select(ScheduleItem).options(
            selectinload(ScheduleItem.lesson).selectinload(Lesson.subject),
            selectinload(ScheduleItem.audience),
            selectinload(ScheduleItem.time_slot)
        )
    )
    items = items_result.scalars().all()
    schedule_data = []
    for item in items:
        lesson = item.lesson
        subject = lesson.subject if lesson else None
        teacher_name = "Не назначен"
        if subject and subject.teachers:
            teacher_name = ", ".join(t.name for t in subject.teachers)
        schedule_data.append({
            "subject": subject.name if subject else "---",
            "teacher": teacher_name,
            "audience": item.audience.name if item.audience else "---",
            "date": str(item.date) if item.date else "---",
            "pair": item.time_slot.slot_number if item.time_slot else None,
            "time": f"{item.time_slot.start_time} - {item.time_slot.end_time}" if item.time_slot else "---"
        })
    return schedule_data

@router.post("/pin/{item_id}")
async def pin_item(item_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScheduleItem).where(ScheduleItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    item.is_pinned = not item.is_pinned
    await db.commit()
    return {"is_pinned": item.is_pinned}

@router.post("/approve")
async def approve_schedule(db: AsyncSession = Depends(get_db)):
    # Очистить финальное расписание
    await db.execute(delete(FinalScheduleItem))
    # Скопировать все черновики (без закреплённых? обычно копируются все)
    drafts_result = await db.execute(select(ScheduleItem))
    drafts = drafts_result.scalars().all()
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

@router.post("/generate")
@router.get("/generate")  # добавить эту строку
async def generate(db: AsyncSession = Depends(get_db)):
    result = await generate_schedule(db)
    if result["count"] == 0:
        return {"status": "error", "message": "Недостаточно данных"}
    return result