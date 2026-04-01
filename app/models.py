from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date, Time, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .database import Base
import datetime

# --- ТАБЛИЦЫ СВЯЗЕЙ (Связь теперь через subject_id) ---
op_groups_of_pairs = Table(
    'op_groups_of_pairs',
    Base.metadata,
    Column('group_id', Integer, ForeignKey('ref_groups.id'), primary_key=True),
    Column('subject_id', Integer, ForeignKey('ref_subject.id'), primary_key=True)
)

op_teachers_of_pairs = Table(
    'op_teachers_of_pairs',
    Base.metadata,
    Column('teacher_id', Integer, ForeignKey('ref_teachers.id'), primary_key=True),
    Column('subject_id', Integer, ForeignKey('ref_subject.id'), primary_key=True),
    Column('is_main', Boolean, default=True)
)

# --- СПРАВОЧНИКИ (ref_*) ---
class Subject(Base):
    __tablename__ = "ref_subject"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    
    # Группы и преподаватели теперь привязаны к самому предмету
    groups = relationship("Group", secondary=op_groups_of_pairs)
    teachers = relationship("Teacher", secondary=op_teachers_of_pairs)

class Audience(Base):
    __tablename__ = "ref_audiences"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    capacity: Mapped[int] = mapped_column(Integer) 
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class Group(Base):
    __tablename__ = "ref_groups"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String) 
    student_count: Mapped[int] = mapped_column(Integer, nullable=True) 

class Teacher(Base):
    __tablename__ = "ref_teachers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String) 

class TimeSlot(Base):
    __tablename__ = "ref_time_slots"
    id: Mapped[int] = mapped_column(primary_key=True)
    slot_number: Mapped[int] = mapped_column(Integer) 
    name: Mapped[str] = mapped_column(String) 
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)     

# --- ОПЕРАЦИОННЫЕ ДАННЫЕ (op_*) ---
class Lesson(Base):
    __tablename__ = "op_lessons"
    id: Mapped[int] = mapped_column(primary_key=True)
    subject_id: Mapped[int] = mapped_column(Integer, ForeignKey('ref_subject.id')) # Ссылка на Subject
    date: Mapped[datetime.date] = mapped_column(Date) 
    student_count: Mapped[int] = mapped_column(Integer, nullable=True) 
    time_slot_id: Mapped[int] = mapped_column(Integer, ForeignKey('ref_time_slots.id'), nullable=True)
    
    # Отношение к Subject
    subject = relationship("Subject")

# В models.py

# app/models.py

class ScheduleItem(Base):
    __tablename__ = "op_schedule_items_1"
    id: Mapped[int] = mapped_column(primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey('op_lessons.id'))
    time_slot_id: Mapped[int] = mapped_column(ForeignKey('ref_time_slots.id'))
    audience_id: Mapped[int] = mapped_column(ForeignKey('ref_audiences.id'))
    date: Mapped[datetime.date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String, default='scheduled')
    # ДОБАВЬ ЭТУ СТРОКУ:
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False) 

    lesson = relationship("Lesson")
    time_slot = relationship("TimeSlot")
    audience = relationship("Audience")

# ДОБАВЬ ВЕСЬ ЭТОТ КЛАСС В КОНЕЦ ФАЙЛА:
class FinalScheduleItem(Base):
    __tablename__ = "op_final_schedule"
    id: Mapped[int] = mapped_column(primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey('op_lessons.id'))
    time_slot_id: Mapped[int] = mapped_column(ForeignKey('ref_time_slots.id'))
    audience_id: Mapped[int] = mapped_column(ForeignKey('ref_audiences.id'))
    date: Mapped[datetime.date] = mapped_column(Date)

    lesson = relationship("Lesson")
    time_slot = relationship("TimeSlot")
    audience = relationship("Audience")