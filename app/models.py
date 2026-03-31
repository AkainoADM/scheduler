from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date, Time, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column, relationship, joinedload
from .database import Base
from datetime import date, time
from .database import Base
import datetime
# --- ТАБЛИЦЫ СВЯЗЕЙ (Many-to-Many) [cite: 52, 55, 58] ---
op_groups_of_pairs = Table(
    'op_groups_of_pairs',
    Base.metadata,
    Column('group_id', Integer, ForeignKey('ref_groups.id'), primary_key=True),
    Column('lesson_id', Integer, ForeignKey('op_lessons.id'), primary_key=True)
)

op_teachers_of_pairs = Table(
    'op_teachers_of_pairs',
    Base.metadata,
    Column('teacher_id', Integer, ForeignKey('ref_teachers.id'), primary_key=True),
    Column('lesson_id', Integer, ForeignKey('op_lessons.id'), primary_key=True),
    Column('is_main', Boolean, default=True)
)

# --- СПРАВОЧНИКИ (ref_*) [cite: 21, 27, 29, 32] ---
class Audience(Base):
    __tablename__ = "ref_audiences"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    capacity: Mapped[int] = mapped_column(Integer) # Вместимость [cite: 102]
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

# Операционные данные (op_*) [cite: 122]
class Lesson(Base):
    __tablename__ = "op_lessons"
    id: Mapped[int] = mapped_column(primary_key=True)
    subject: Mapped[str] = mapped_column(String) # [cite: 50]
    date: Mapped[datetime.date] = mapped_column(Date) # [cite: 50]
    student_count: Mapped[int] = mapped_column(Integer) # [cite: 50]
    time_slot_id: Mapped[int] = mapped_column(Integer, ForeignKey('ref_time_slots.id'), nullable=True)
    # Отношения для доступа к данным в генераторе
    groups = relationship("Group", secondary=op_groups_of_pairs)
    teachers = relationship("Teacher", secondary=op_teachers_of_pairs)
class ScheduleItem(Base):
    __tablename__ = "op_schedule_items_1"
    id: Mapped[int] = mapped_column(primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey('op_lessons.id'))
    time_slot_id: Mapped[int] = mapped_column(ForeignKey('ref_time_slots.id'))
    audience_id: Mapped[int] = mapped_column(ForeignKey('ref_audiences.id'))
    date: Mapped[datetime.date] = mapped_column(Date) # Денормализация [cite: 144]
    status: Mapped[str] = mapped_column(String, default='scheduled')

    lesson = relationship("Lesson")
    time_slot = relationship("TimeSlot")
    audience = relationship("Audience")
class Group(Base):
    __tablename__ = "ref_groups"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String) # [cite: 28]
    student_count: Mapped[int] = mapped_column(Integer) # Используется в utils.py [cite: 28]
class Teacher(Base):
    __tablename__ = "ref_teachers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String) # [cite: 31]
class TimeSlot(Base):
    __tablename__ = "ref_time_slots"
    id: Mapped[int] = mapped_column(primary_key=True)
    slot_number: Mapped[int] = mapped_column(Integer) # [cite: 34]
    name: Mapped[str] = mapped_column(String) # [cite: 34]
    is_active: Mapped[bool] = mapped_column(Boolean, default=True) # [cite: 34]    