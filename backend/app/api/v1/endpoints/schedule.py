from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from app.core.database import get_db
from backend.app.models.schedule_models import ScheduleItem, Lesson
from backend.app.models.schedule_models import Audience, Group, Subject, TimeSlot

router = APIRouter(prefix="/schedule", tags=["Schedule"])


# -----------------------
# Pydantic схемы
# -----------------------
class LessonCreate(BaseModel):
    subject_id: int
    date: str  # YYYY-MM-DD
    time_slot_id: int
    text: Optional[str] = None


class LessonUpdate(BaseModel):
    subject_id: Optional[int] = None
    date: Optional[str] = None
    time_slot_id: Optional[int] = None
    text: Optional[str] = None


class ScheduleItemCreate(BaseModel):
    lesson_id: int
    audience_id: int
    date: Optional[str] = None  # YYYY-MM-DD
    time_slot_id: Optional[int] = None


class ScheduleItemUpdate(BaseModel):
    audience_id: Optional[int] = None
    date: Optional[str] = None
    time_slot_id: Optional[int] = None
    is_pinned: Optional[bool] = None


# -----------------------
# Lessons CRUD
# -----------------------
@router.post("/lessons", response_model=dict)
async def create_lesson(payload: LessonCreate, db: AsyncSession = Depends(get_db)):
    subj = await db.get(Subject, payload.subject_id)
    if not subj:
        raise HTTPException(status_code=404, detail="Subject not found")
    ts = await db.get(TimeSlot, payload.time_slot_id)
    if not ts:
        raise HTTPException(status_code=404, detail="Time slot not found")
    try:
        date_obj = datetime.strptime(payload.date, "%Y-%m-%d").date()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date format, expected YYYY-MM-DD")

    lesson = Lesson(
        text=payload.text or "",
        date=date_obj,
        subject_id=payload.subject_id,
        time_slot_id=payload.time_slot_id
    )
    db.add(lesson)
    await db.commit()
    await db.refresh(lesson)
    return {"id": lesson.id, "subject_id": lesson.subject_id, "date": str(lesson.date), "time_slot_id": lesson.time_slot_id}


@router.put("/lessons/{lesson_id}", response_model=dict)
async def update_lesson(lesson_id: int, payload: LessonUpdate, db: AsyncSession = Depends(get_db)):
    lesson = await db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    if payload.subject_id is not None:
        subj = await db.get(Subject, payload.subject_id)
        if not subj:
            raise HTTPException(status_code=404, detail="Subject not found")
        lesson.subject_id = payload.subject_id
    if payload.time_slot_id is not None:
        ts = await db.get(TimeSlot, payload.time_slot_id)
        if not ts:
            raise HTTPException(status_code=404, detail="Time slot not found")
        lesson.time_slot_id = payload.time_slot_id
    if payload.date is not None:
        try:
            lesson.date = datetime.strptime(payload.date, "%Y-%m-%d").date()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid date format")
    if payload.text is not None:
        lesson.text = payload.text
    await db.commit()
    await db.refresh(lesson)
    return {"id": lesson.id}


@router.delete("/lessons/{lesson_id}")
async def delete_lesson(lesson_id: int, db: AsyncSession = Depends(get_db)):
    # удаляем связанные schedule items, затем lesson
    await db.execute(delete(ScheduleItem).where(ScheduleItem.lesson_id == lesson_id))
    await db.execute(delete(Lesson).where(Lesson.id == lesson_id))
    await db.commit()
    return {"ok": True}


# -----------------------
# ScheduleItem CRUD
# -----------------------
@router.post("/item", response_model=dict)
async def create_schedule_item(payload: ScheduleItemCreate, db: AsyncSession = Depends(get_db)):
    lesson = await db.get(Lesson, payload.lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    aud = await db.get(Audience, payload.audience_id)
    if not aud:
        raise HTTPException(status_code=404, detail="Audience not found")

    if payload.date:
        try:
            date_obj = datetime.strptime(payload.date, "%Y-%m-%d").date()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid date format")
    else:
        date_obj = lesson.date

    time_slot_id = payload.time_slot_id or lesson.time_slot_id

    item = ScheduleItem(
        lesson_id=payload.lesson_id,
        time_slot_id=time_slot_id,
        audience_id=payload.audience_id,
        date=date_obj,
        status="OK",
        is_pinned=False
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return {"id": item.id}


@router.put("/item/{item_id}", response_model=dict)
async def update_schedule_item(item_id: int, payload: ScheduleItemUpdate, db: AsyncSession = Depends(get_db)):
    item = await db.get(ScheduleItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    if payload.audience_id is not None:
        aud = await db.get(Audience, payload.audience_id)
        if not aud:
            raise HTTPException(status_code=404, detail="Audience not found")
        item.audience_id = payload.audience_id
    if payload.time_slot_id is not None:
        ts = await db.get(TimeSlot, payload.time_slot_id)
        if not ts:
            raise HTTPException(status_code=404, detail="Time slot not found")
        item.time_slot_id = payload.time_slot_id
    if payload.date is not None:
        try:
            item.date = datetime.strptime(payload.date, "%Y-%m-%d").date()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid date format")
    if payload.is_pinned is not None:
        item.is_pinned = payload.is_pinned
    await db.commit()
    await db.refresh(item)
    return {"id": item.id, "is_pinned": bool(item.is_pinned)}


@router.delete("/item/{item_id}")
async def delete_schedule_item(item_id: int, db: AsyncSession = Depends(get_db)):
    await db.execute(delete(ScheduleItem).where(ScheduleItem.id == item_id))
    await db.commit()
    return {"ok": True}


@router.post("/item/move")
async def move_schedule_item(payload: dict, db: AsyncSession = Depends(get_db)):
    """
    payload: { "item_id": int, "date": "YYYY-MM-DD", "time_slot_id": int, "audience_id": int }
    """
    item_id = payload.get("item_id")
    if not item_id:
        raise HTTPException(status_code=400, detail="item_id required")
    item = await db.get(ScheduleItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    if "date" in payload and payload["date"]:
        try:
            item.date = datetime.strptime(payload["date"], "%Y-%m-%d").date()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid date")
    if "time_slot_id" in payload and payload["time_slot_id"] is not None:
        ts = await db.get(TimeSlot, payload["time_slot_id"])
        if not ts:
            raise HTTPException(status_code=404, detail="Time slot not found")
        item.time_slot_id = payload["time_slot_id"]
    if "audience_id" in payload and payload["audience_id"] is not None:
        aud = await db.get(Audience, payload["audience_id"])
        if not aud:
            raise HTTPException(status_code=404, detail="Audience not found")
        item.audience_id = payload["audience_id"]
    await db.commit()
    await db.refresh(item)
    return {"id": item.id}


@router.post("/item/pin/{item_id}")
async def pin_item(item_id: int, db: AsyncSession = Depends(get_db)):
    item = await db.get(ScheduleItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    item.is_pinned = not bool(item.is_pinned)
    await db.commit()
    return {"id": item.id, "is_pinned": bool(item.is_pinned)}