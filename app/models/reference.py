from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date, Time, Table, JSON, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
import datetime

# ---------- Связующие таблицы (многие-ко-многим) ----------
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

# ---------- Справочники ----------
class Subject(Base):
    __tablename__ = "ref_subject"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)

    groups = relationship("Group", secondary=op_groups_of_pairs, backref="subjects")
    teachers = relationship("Teacher", secondary=op_teachers_of_pairs, backref="subjects")

class Audience(Base):
    __tablename__ = "ref_audiences"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    building_id = Column(Integer, ForeignKey('ref_buildings.id'))
    capacity = Column(Integer)
    type = Column(String)   # лекционная, практическая, лабораторная, компьютерный класс
    is_active = Column(Boolean, default=True)

    building = relationship("Building", backref="audiences")

class Building(Base):
    __tablename__ = "ref_buildings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    address = Column(String)

class Calendar(Base):
    __tablename__ = "ref_calendar"
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, unique=True)
    is_working_day = Column(Boolean, default=True)
    week_type = Column(String)
    description = Column(String)

class Faculty(Base):
    __tablename__ = "ref_faculties"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    display_name = Column(String)
    short_display_name = Column(String)

class Group(Base):
    __tablename__ = "ref_groups"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    faculty_id = Column(Integer, ForeignKey('ref_faculties.id'))
    student_count = Column(Integer)

    faculty = relationship("Faculty", backref="groups")

class Teacher(Base):
    __tablename__ = "ref_teachers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    login = Column(String, unique=True)
    name = Column(String)
    url = Column(String)
    # max_hours_per_day/week отсутствуют в новой БД

class TimeSlot(Base):
    __tablename__ = "ref_time_slots"
    id = Column(Integer, primary_key=True, autoincrement=True)
    slot_number = Column(Integer)
    name = Column(String)
    start_time = Column(Time)
    end_time = Column(Time)
    duration_minutes = Column(Integer)
    break_after_minutes = Column(Integer)
    is_active = Column(Boolean, default=True)

class UserType(Base):
    __tablename__ = "ref_user_types"
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, unique=True)
    name = Column(String)
    description = Column(String)

class Role(Base):
    __tablename__ = "ref_roles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String, unique=True)
    description = Column(String)

class Permission(Base):
    __tablename__ = "ref_permissions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    permission_code = Column(String, unique=True)
    permission_name = Column(String)
    description = Column(String)

class Subdivision(Base):
    __tablename__ = "ref_subdivisions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)

class User(Base):
    __tablename__ = "ref_users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    password_hash = Column(String)
    full_name = Column(String)
    user_type_id = Column(Integer, ForeignKey('ref_user_types.id'))
    is_active = Column(Boolean)
    created_at = Column(DateTime)
    last_login = Column(DateTime)

    user_type = relationship("UserType")

# ---------- Операционные таблицы для расписания ----------
class Lesson(Base):
    __tablename__ = "op_lessons"
    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(Integer, ForeignKey('ref_subject.id'))
    date = Column(Date)
    student_count = Column(Integer)
    time_slot_id = Column(Integer, ForeignKey('ref_time_slots.id'), nullable=True)

    subject = relationship("Subject")
    time_slot = relationship("TimeSlot")

class ScheduleItem(Base):
    __tablename__ = "op_schedule_items_1"
    id = Column(Integer, primary_key=True, autoincrement=True)
    lesson_id = Column(Integer, ForeignKey('op_lessons.id'))
    time_slot_id = Column(Integer, ForeignKey('ref_time_slots.id'))
    audience_id = Column(Integer, ForeignKey('ref_audiences.id'))
    date = Column(Date)
    status = Column(String, default='scheduled')
    is_pinned = Column(Boolean, default=False)

    lesson = relationship("Lesson")
    time_slot = relationship("TimeSlot")
    audience = relationship("Audience")

class FinalScheduleItem(Base):
    __tablename__ = "op_final_schedule"
    id = Column(Integer, primary_key=True, autoincrement=True)
    lesson_id = Column(Integer, ForeignKey('op_lessons.id'))
    time_slot_id = Column(Integer, ForeignKey('ref_time_slots.id'))
    audience_id = Column(Integer, ForeignKey('ref_audiences.id'))
    date = Column(Date)

    lesson = relationship("Lesson")
    time_slot = relationship("TimeSlot")
    audience = relationship("Audience")

class TemplateItem(Base):
    __tablename__ = "op_templates"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name_of_sample_id = Column(Integer, ForeignKey('op_name_of_sample.id'))
    day_of_week_id = Column(Integer, ForeignKey('ref_days_of_the_week.id'))
    time_slot_id = Column(Integer, ForeignKey('ref_time_slots.id'))
    lesson_id = Column(Integer, ForeignKey('op_lessons.id'))
    audience_id = Column(Integer, ForeignKey('ref_audiences.id'))

class DayOfWeek(Base):
    __tablename__ = "ref_days_of_the_week"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)

class TemplateName(Base):
    __tablename__ = "op_name_of_sample"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)


from sqlalchemy import Table, Column, Integer, Boolean, ForeignKey

# ... (остальные модели)

# Связующие таблицы
op_teachers_groups = Table(
    'op_teachers_groups',
    Base.metadata,
    Column('teachers_id', Integer, ForeignKey('ref_teachers.id'), primary_key=True),
    Column('groups_id', Integer, ForeignKey('ref_groups.id'), primary_key=True),
    extend_existing=True
)

op_teachers_of_pairs = Table(
    'op_teachers_of_pairs',
    Base.metadata,
    Column('teacher_id', Integer, ForeignKey('ref_teachers.id'), primary_key=True),
    Column('subject_id', Integer, ForeignKey('ref_subject.id'), primary_key=True),
    Column('is_main', Boolean, default=False),
    extend_existing=True
)

op_audiences_of_pairs = Table(
    'op_audiences_of_pairs',
    Base.metadata,
    Column('audience_id', Integer, ForeignKey('ref_audiences.id'), primary_key=True),
    Column('subject_id', Integer, ForeignKey('ref_subject.id'), primary_key=True),
    extend_existing=True
)

op_groups_of_pairs = Table(
    'op_groups_of_pairs',
    Base.metadata,
    Column('group_id', Integer, ForeignKey('ref_groups.id'), primary_key=True),
    Column('subject_id', Integer, ForeignKey('ref_subject.id'), primary_key=True),
    extend_existing=True
)