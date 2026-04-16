from __future__ import annotations
from typing import Optional, List
from datetime import date, datetime, time
from sqlalchemy import (
    Table,
    Column,
    ForeignKey,
    Integer,
    String,
    Boolean,
    Date,
    Time,
    JSON,
    DateTime,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base 
op_groups_of_pairs = Table(
    "op_groups_of_pairs",
    Base.metadata,
    Column("group_id", Integer, ForeignKey("ref_groups.id"), primary_key=True),
    Column("subject_id", Integer, ForeignKey("ref_subject.id"), primary_key=True),
)

op_teachers_of_pairs = Table(
    "op_teachers_of_pairs",
    Base.metadata,
    Column("teacher_id", Integer, ForeignKey("ref_teachers.id"), primary_key=True),
    Column("subject_id", Integer, ForeignKey("ref_subject.id"), primary_key=True),
    Column("is_main", Boolean, default=True),
)

op_teachers_groups = Table(
    "op_teachers_groups",
    Base.metadata,
    Column("teachers_id", Integer, ForeignKey("ref_teachers.id"), primary_key=True),
    Column("groups_id", Integer, ForeignKey("ref_groups.id"), primary_key=True),
    extend_existing=True,
)

op_audiences_of_pairs = Table(
    "op_audiences_of_pairs",
    Base.metadata,
    Column("audience_id", Integer, ForeignKey("ref_audiences.id"), primary_key=True),
    Column("subject_id", Integer, ForeignKey("ref_subject.id"), primary_key=True),
    extend_existing=True,
)


# ---------- Справочники (ref_*) ----------
class Subject(Base):
    __tablename__ = "ref_subject"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=False)

    groups: Mapped[List["Group"]] = relationship(
        "Group", secondary=op_groups_of_pairs, back_populates="subjects"
    )
    teachers: Mapped[List["Teacher"]] = relationship(
        "Teacher", secondary=op_teachers_of_pairs, back_populates="subjects"
    )


class Audience(Base):
    __tablename__ = "ref_audiences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    building_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("ref_buildings.id"), nullable=True)
    capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)

    building: Mapped[Optional["Building"]] = relationship("Building", back_populates="audiences")


class Building(Base):
    __tablename__ = "ref_buildings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    audiences: Mapped[List[Audience]] = relationship("Audience", back_populates="building")


class Calendar(Base):
    __tablename__ = "ref_calendar"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, unique=True)
    is_working_day: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    week_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class Faculty(Base):
    __tablename__ = "ref_faculties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    display_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    short_display_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class Group(Base):
    __tablename__ = "ref_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    faculty_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("ref_faculties.id"), nullable=True)
    student_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    faculty: Mapped[Optional[Faculty]] = relationship("Faculty", back_populates="groups")
    subjects: Mapped[List[Subject]] = relationship(
        "Subject", secondary=op_groups_of_pairs, back_populates="groups"
    )
    teachers: Mapped[List["Teacher"]] = relationship(
        "Teacher", secondary=op_teachers_groups, back_populates="groups"
    )


Faculty.groups = relationship("Group", back_populates="faculty")


class Teacher(Base):
    __tablename__ = "ref_teachers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    login: Mapped[Optional[str]] = mapped_column(String, nullable=True, unique=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    subjects: Mapped[List[Subject]] = relationship(
        "Subject", secondary=op_teachers_of_pairs, back_populates="teachers"
    )
    groups: Mapped[List[Group]] = relationship(
        "Group", secondary=op_teachers_groups, back_populates="teachers"
    )


class TimeSlot(Base):
    __tablename__ = "ref_time_slots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slot_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    start_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    end_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    break_after_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)


class UserType(Base):
    __tablename__ = "ref_user_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[Optional[str]] = mapped_column(String, nullable=True, unique=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class Role(Base):
    __tablename__ = "ref_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_name: Mapped[Optional[str]] = mapped_column(String, nullable=True, unique=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class Permission(Base):
    __tablename__ = "ref_permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    permission_code: Mapped[Optional[str]] = mapped_column(String, nullable=True, unique=True)
    permission_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class Subdivision(Base):
    __tablename__ = "ref_subdivisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class User(Base):
    __tablename__ = "ref_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[Optional[str]] = mapped_column(String, nullable=True, unique=True)
    email: Mapped[Optional[str]] = mapped_column(String, nullable=True, unique=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    user_type_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("ref_user_types.id"), nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user_type: Mapped[Optional[UserType]] = relationship("UserType")


# ---------- Операционные таблицы для расписания (op_*) ----------
class Lesson(Base):
    __tablename__ = "op_lessons"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("ref_subject.id"), nullable=True)
    date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    student_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    time_slot_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("ref_time_slots.id"), nullable=True)
    week_day: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    text: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    type: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    subject: Mapped[Optional[Subject]] = relationship("Subject", lazy="joined", back_populates="lessons")
    schedule_items: Mapped[List["ScheduleItem"]] = relationship("ScheduleItem", back_populates="lesson")


# добавить обратную связь на Subject.lessons
Subject.lessons = relationship("Lesson", back_populates="subject")


class ScheduleItem(Base):
    __tablename__ = "op_schedule_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lesson_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("op_lessons.id"), nullable=True)
    time_slot_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("ref_time_slots.id"), nullable=True)
    audience_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("ref_audiences.id"), nullable=True)
    date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String, nullable=True, default="scheduled")
    is_pinned: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    lesson: Mapped[Optional[Lesson]] = relationship("Lesson", back_populates="schedule_items", lazy="joined")
    time_slot: Mapped[Optional[TimeSlot]] = relationship("TimeSlot", lazy="joined")
    audience: Mapped[Optional[Audience]] = relationship("Audience", lazy="joined")


class FinalScheduleItem(Base):
    __tablename__ = "op_final_schedule"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lesson_id: Mapped[int] = mapped_column(Integer, ForeignKey("op_lessons.id"), nullable=False)
    time_slot_id: Mapped[int] = mapped_column(Integer, ForeignKey("ref_time_slots.id"), nullable=False)
    audience_id: Mapped[int] = mapped_column(Integer, ForeignKey("ref_audiences.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)

    lesson: Mapped[Optional[Lesson]] = relationship("Lesson", lazy="joined")
    time_slot: Mapped[Optional[TimeSlot]] = relationship("TimeSlot", lazy="joined")
    audience: Mapped[Optional[Audience]] = relationship("Audience", lazy="joined")


class DayOfWeek(Base):
    __tablename__ = "ref_days_of_the_week"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class TemplateName(Base):
    __tablename__ = "op_name_of_sample"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)


# ---------- Шаблоны ----------
class Template(Base):
    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    faculty_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("ref_faculties.id"), nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)

    lessons: Mapped[List["TemplateLesson"]] = relationship("TemplateLesson", back_populates="template")


class TemplateLesson(Base):
    __tablename__ = "template_lessons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(Integer, ForeignKey("templates.id"), nullable=False)
    subject_id: Mapped[int] = mapped_column(Integer, ForeignKey("ref_subject.id"), nullable=False)
    group_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("ref_groups.id"), nullable=True)
    teacher_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("ref_teachers.id"), nullable=True)
    audience_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("ref_audiences.id"), nullable=True)
    time_slot_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("ref_time_slots.id"), nullable=True)
    date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    week_day: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    week_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    duration: Mapped[int] = mapped_column(Integer, default=1)

    template: Mapped[Template] = relationship("Template", back_populates="lessons")
    subject: Mapped[Subject] = relationship("Subject", lazy="joined")
    group: Mapped[Group] = relationship("Group", lazy="joined")
    teacher: Mapped[Teacher] = relationship("Teacher", lazy="joined")
    audience: Mapped[Audience] = relationship("Audience", lazy="joined")
    time_slot: Mapped[TimeSlot] = relationship("TimeSlot", lazy="joined")


# ---------- Правила ----------
class SchedulingRule(Base):
    __tablename__ = "scheduling_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    rule_type: Mapped[str] = mapped_column(String, nullable=False)  # 'teacher', 'group', 'audience', 'common'
    is_hard: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    condition_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class RuleScopeTeacher(Base):
    __tablename__ = "rule_scope_teachers"

    rule_id: Mapped[int] = mapped_column(Integer, ForeignKey("scheduling_rules.id"), primary_key=True)
    teacher_id: Mapped[int] = mapped_column(Integer, ForeignKey("ref_teachers.id"), primary_key=True)


class RuleScopeGroup(Base):
    __tablename__ = "rule_scope_groups"

    rule_id: Mapped[int] = mapped_column(Integer, ForeignKey("scheduling_rules.id"), primary_key=True)
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("ref_groups.id"), primary_key=True)


class RuleScopeAudience(Base):
    __tablename__ = "rule_scope_audiences"

    rule_id: Mapped[int] = mapped_column(Integer, ForeignKey("scheduling_rules.id"), primary_key=True)
    audience_id: Mapped[int] = mapped_column(Integer, ForeignKey("ref_audiences.id"), primary_key=True)
