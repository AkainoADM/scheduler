# app/schemas/lesson.py
from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import Optional

class LessonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject_id: int
    date: date
    student_count: Optional[int] = None
    time_slot_id: Optional[int] = None
    week_day: Optional[int] = None
    text: Optional[str] = None
    type: Optional[str] = None
    group_id: Optional[int] = None

class LessonCreate(BaseModel):
    subject_id: int
    date: date
    student_count: Optional[int] = None
    time_slot_id: Optional[int] = None
    text: Optional[str] = None
    type: Optional[str] = None
    group_id: Optional[int] = None

class LessonUpdate(BaseModel):
    subject_id: Optional[int] = None
    date: Optional[date] = None
    student_count: Optional[int] = None
    time_slot_id: Optional[int] = None
    text: Optional[str] = None
    type: Optional[str] = None
    group_id: Optional[int] = None