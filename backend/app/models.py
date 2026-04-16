from __future__ import annotations
from typing import Optional
from datetime import date, time
from sqlalchemy import Integer, String, Boolean, Date, Time, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base  
class RefGroup(Base):
    __tablename__ = "ref_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String)
    faculty_id: Mapped[Optional[int]] = mapped_column(Integer)
    student_count: Mapped[Optional[int]] = mapped_column(Integer)


class RefTeacher(Base):
    __tablename__ = "ref_teachers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    login: Mapped[Optional[str]] = mapped_column(String)
    name: Mapped[Optional[str]] = mapped_column(String)
    max_hours_per_day: Mapped[Optional[int]] = mapped_column(Integer)
    max_hours_per_week: Mapped[Optional[int]] = mapped_column(Integer)




class RefTimeSlot(Base):
    __tablename__ = "ref_time_slots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slot_number: Mapped[Optional[int]] = mapped_column(Integer)
    name: Mapped[Optional[str]] = mapped_column(String)
    start_time: Mapped[Optional[time]] = mapped_column(Time)
    end_time: Mapped[Optional[time]] = mapped_column(Time)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean)


class RefAudience(Base):
    __tablename__ = "ref_audiences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String)
    capacity: Mapped[Optional[int]] = mapped_column(Integer)
    type: Mapped[Optional[str]] = mapped_column(String)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean)


class RefCalendar(Base):
    __tablename__ = "ref_calendar"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    calendar_date: Mapped[Optional[date]] = mapped_column(Date, nullable=False)
    is_working_day: Mapped[Optional[bool]] = mapped_column(Boolean)
    week_type: Mapped[Optional[str]] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(String)


# -------------------------
# Template records (op_templates)
# -------------------------
class OpTemplate(Base):
    __tablename__ = "op_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_of_sample_id: Mapped[Optional[int]] = mapped_column(Integer)
    day_of_week_id: Mapped[Optional[int]] = mapped_column(Integer)
    time_slot_id: Mapped[Optional[int]] = mapped_column(Integer)
    lesson_id: Mapped[Optional[int]] = mapped_column(Integer)
    audience_id: Mapped[Optional[int]] = mapped_column(Integer)


# -------------------------
# Generated lesson (op_lessons)
# -------------------------
class OpLesson(Base):
    __tablename__ = "op_lessons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[Optional[str]] = mapped_column(String, default="")
    # поле даты урока — переименовано, чтобы не конфликтовать с типом Date
    lesson_date: Mapped[Optional[date]] = mapped_column(Date)
    subject_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ref_subject.id"))
    insertion_id: Mapped[Optional[int]] = mapped_column(Integer)
    time_slot_id: Mapped[Optional[int]] = mapped_column(Integer)
    week_day: Mapped[Optional[int]] = mapped_column(Integer)
    type: Mapped[Optional[str]] = mapped_column(String)
    student_count: Mapped[Optional[int]] = mapped_column(Integer)

    # Примеры отношений (если нужны)
    subject = relationship("RefSubject", lazy="joined", backref="lessons")


# -------------------------
# Schedule item (op_schedule_items)
# -------------------------
class OpScheduleItem(Base):
    __tablename__ = "op_schedule_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_id: Mapped[Optional[int]] = mapped_column(ForeignKey("op_lessons.id"))
    time_slot_id: Mapped[Optional[int]] = mapped_column(Integer)
    audience_id: Mapped[Optional[int]] = mapped_column(Integer)
    item_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[Optional[str]] = mapped_column(String)
    is_pinned: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    lesson = relationship("OpLesson", lazy="joined", backref="schedule_items")
