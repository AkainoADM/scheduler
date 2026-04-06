# app/models/schedule_models.py
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Time, Boolean, JSON, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
import datetime

# Связующие таблицы
op_groups_of_pairs = Table(
    'op_groups_of_pairs', Base.metadata,
    Column('group_id', Integer, ForeignKey('ref_groups.id'), primary_key=True),
    Column('subject_id', Integer, ForeignKey('ref_subject.id'), primary_key=True)
)

op_teachers_of_pairs = Table(
    'op_teachers_of_pairs', Base.metadata,
    Column('teacher_id', Integer, ForeignKey('ref_teachers.id'), primary_key=True),
    Column('subject_id', Integer, ForeignKey('ref_subject.id'), primary_key=True),
    Column('is_main', Boolean, default=True)
)

class Subject(Base):
    __tablename__ = "ref_subject"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    # связи
    groups = relationship("Group", secondary=op_groups_of_pairs, backref="subjects")
    teachers = relationship("Teacher", secondary=op_teachers_of_pairs, backref="subjects")

class Lesson(Base):
    __tablename__ = "op_lessons"
    id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, ForeignKey('ref_subject.id'), nullable=False)
    date = Column(Date, nullable=False)
    student_count = Column(Integer, nullable=True)
    time_slot_id = Column(Integer, ForeignKey('ref_time_slots.id'), nullable=True)
    subject = relationship("Subject")

class ScheduleItem(Base):
    __tablename__ = "op_schedule_items_1"   # обратите внимание на имя таблицы
    id = Column(Integer, primary_key=True)
    lesson_id = Column(Integer, ForeignKey('op_lessons.id'), nullable=False)
    time_slot_id = Column(Integer, ForeignKey('ref_time_slots.id'), nullable=False)
    audience_id = Column(Integer, ForeignKey('ref_audiences.id'), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(String, default='scheduled')
    is_pinned = Column(Boolean, default=False)
    lesson = relationship("Lesson")
    time_slot = relationship("TimeSlot")
    audience = relationship("Audience")

class FinalScheduleItem(Base):
    __tablename__ = "op_final_schedule"
    id = Column(Integer, primary_key=True)
    lesson_id = Column(Integer, ForeignKey('op_lessons.id'), nullable=False)
    time_slot_id = Column(Integer, ForeignKey('ref_time_slots.id'), nullable=False)
    audience_id = Column(Integer, ForeignKey('ref_audiences.id'), nullable=False)
    date = Column(Date, nullable=False)
    lesson = relationship("Lesson")
    time_slot = relationship("TimeSlot")
    audience = relationship("Audience")

# Шаблоны
class Template(Base):
    __tablename__ = "templates"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    faculty_id = Column(Integer, ForeignKey('ref_faculties.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)

class TemplateLesson(Base):
    __tablename__ = "template_lessons"
    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey('templates.id'), nullable=False)
    subject_id = Column(Integer, ForeignKey('ref_subject.id'), nullable=False)
    group_id = Column(Integer, ForeignKey('ref_groups.id'), nullable=True)
    teacher_id = Column(Integer, ForeignKey('ref_teachers.id'), nullable=True)
    audience_id = Column(Integer, ForeignKey('ref_audiences.id'), nullable=True)
    time_slot_id = Column(Integer, ForeignKey('ref_time_slots.id'), nullable=True)
    date = Column(Date, nullable=True)
    week_day = Column(Integer, nullable=True)  # 1-7
    week_type = Column(String, nullable=True)  # 'числитель', 'знаменатель'
    duration = Column(Integer, default=1)
    template = relationship("Template", backref="lessons")
    subject = relationship("Subject")
    group = relationship("Group")
    teacher = relationship("Teacher")
    audience = relationship("Audience")
    time_slot = relationship("TimeSlot")

# Правила
class SchedulingRule(Base):
    __tablename__ = "scheduling_rules"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    rule_type = Column(String, nullable=False)  # 'teacher', 'group', 'audience', 'common'
    is_hard = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    condition_json = Column(JSON, nullable=False)
    description = Column(String)

class RuleScopeTeacher(Base):
    __tablename__ = "rule_scope_teachers"
    rule_id = Column(Integer, ForeignKey('scheduling_rules.id'), primary_key=True)
    teacher_id = Column(Integer, ForeignKey('ref_teachers.id'), primary_key=True)

class RuleScopeGroup(Base):
    __tablename__ = "rule_scope_groups"
    rule_id = Column(Integer, ForeignKey('scheduling_rules.id'), primary_key=True)
    group_id = Column(Integer, ForeignKey('ref_groups.id'), primary_key=True)

class RuleScopeAudience(Base):
    __tablename__ = "rule_scope_audiences"
    rule_id = Column(Integer, ForeignKey('scheduling_rules.id'), primary_key=True)
    audience_id = Column(Integer, ForeignKey('ref_audiences.id'), primary_key=True)