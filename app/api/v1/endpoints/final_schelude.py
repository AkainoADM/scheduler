from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.reference import FinalScheduleItem, Lesson

router = APIRouter(prefix="/final-schedule", tags=["Final Schedule"])

@router.get("/")
async def get_final_schedule(db: AsyncSession = Depends(get_db)):
    items_result = await db.execute(
        select(FinalScheduleItem).options(
            selectinload(FinalScheduleItem.lesson).selectinload(Lesson.subject),
            selectinload(FinalScheduleItem.lesson).selectinload(Lesson.group),
            selectinload(FinalScheduleItem.audience),
            selectinload(FinalScheduleItem.time_slot)
        )
    )
    items = items_result.scalars().all()
    data = []
    for item in items:
        lesson = item.lesson
        subject = lesson.subject if lesson else None
        group = lesson.group if lesson else None
        teacher_names = ", ".join(t.name for t in subject.teachers) if subject and subject.teachers else "Не назначен"
        data.append({
            "id": item.id,
            "subject": subject.name if subject else "---",
            "teacher": teacher_names,
            "group": group.name if group else "Не указана",
            "audience": item.audience.name if item.audience else "---",
            "date": str(item.date),
            "pair": item.time_slot.slot_number if item.time_slot else None,
            "time": f"{item.time_slot.start_time} - {item.time_slot.end_time}" if item.time_slot else "---"
        })
    return data