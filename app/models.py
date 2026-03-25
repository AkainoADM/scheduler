from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date, Time, Table
from sqlalchemy.orm import relationship
from .database import Base

op_audiences_of_pairs = Table(
    'op_audiences_of_pairs', Base.metadata,
    Column('audience_id', Integer, ForeignKey('ref_audiences.id')),
    Column('lesson_id', Integer, ForeignKey('op_lessons.id'))
)

op_groups_of_pairs = Table(
    'op_groups_of_pairs', Base.metadata,
    Column('group_id', Integer, ForeignKey('ref_groups.id')),
    Column('lesson_id', Integer, ForeignKey('op_lessons.id'))
)

op_teachers_of_pairs = Table(
    'op_teachers_of_pairs', Base.metadata,
    Column('teacher_id', Integer, ForeignKey('ref_teachers.id')),
    Column('lesson_id', Integer, ForeignKey('op_lessons.id')),
    Column('is_main', Boolean)
)

# --- СПРАВОЧНИКИ (ref_*) ---
class Audience(Base):
    __tablename__ = "ref_audiences"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    building_id = Column(Integer, ForeignKey('ref_buildings.id'))
    capacity = Column(Integer)
    type = Column(String)
    is_active = Column(Boolean)

class Group(Base):
    __tablename__ = "ref_groups"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    faculty_id = Column(Integer, ForeignKey('ref_faculties.id'))
    student_count = Column(Integer)

class Teacher(Base):
    __tablename__ = "ref_teachers"
    id = Column(Integer, primary_key=True)
    login = Column(String)
    name = Column(String)  # В новой БД ФИО лежит здесь
    max_hours_per_day = Column(Integer)
    max_hours_per_week = Column(Integer)

class TimeSlot(Base):
    __tablename__ = "ref_time_slots"
    id = Column(Integer, primary_key=True)
    slot_number = Column(Integer)
    name = Column(String)
    start_time = Column(Time)
    end_time = Column(Time)

# --- ОПЕРАЦИОННЫЕ ДАННЫЕ (op_*) ---
class Lesson(Base):
    __tablename__ = "op_lessons"
    id = Column(Integer, primary_key=True)
    subject = Column(String)
    date = Column(Date)
    type = Column(String)
    student_count = Column(Integer)
    
    # SQLAlchemy автоматически достанет списки через промежуточные таблицы
    audiences = relationship("Audience", secondary=op_audiences_of_pairs)
    groups = relationship("Group", secondary=op_groups_of_pairs)
    teachers = relationship("Teacher", secondary=op_teachers_of_pairs)

class ScheduleItem(Base):
    __tablename__ = "op_schedule_items"
    id = Column(Integer, primary_key=True)
    lesson_id = Column(Integer, ForeignKey('op_lessons.id'))
    time_slot_id = Column(Integer, ForeignKey('ref_time_slots.id'))
    audience_id = Column(Integer, ForeignKey('ref_audiences.id'))
    date = Column(Date)
    status = Column(String)
    
    # Связи для удобного доступа к объектам при рендеринге
    lesson = relationship("Lesson")
    time_slot = relationship("TimeSlot")
    audience = relationship("Audience")