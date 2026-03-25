from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base

class Faculty(Base):
    """Справочник факультетов"""
    __tablename__ = "ref_faculties"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    
    groups = relationship("Group", back_populates="faculty")

class Building(Base):
    """Справочник корпусов/зданий"""
    __tablename__ = "ref_buildings"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    address = Column(Text)
    
    audiences = relationship("Audience", back_populates="building")

class User(Base):
    """Справочник пользователей (включая преподавателей)"""
    __tablename__ = "ref_users"
    id = Column(Integer, primary_key=True)
    full_name = Column(String(255), nullable=False)
    user_type_id = Column(Integer) 

class Group(Base):
    """Справочник групп"""
    __tablename__ = "ref_groups"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    student_count = Column(Integer, default=0)
    faculty_id = Column(Integer, ForeignKey("ref_faculties.id"))
    
    faculty = relationship("Faculty", back_populates="groups")

class Audience(Base):
    """Справочник аудиторий"""
    __tablename__ = "ref_audiences"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    capacity = Column(Integer)
    building_id = Column(Integer, ForeignKey("ref_buildings.id"))
    
    building = relationship("Building", back_populates="audiences")

class Discipline(Base):
    """Справочник дисциплин """
    __tablename__ = "ref_disciplines"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    teacher_id = Column(Integer, ForeignKey("ref_teachers.id"))


class Timetable(Base):
    """Основная таблица расписания (Черновик/Публикация)"""
    __tablename__ = "op_timetable"
    id = Column(Integer, primary_key=True, index=True)
    discipline_id = Column(Integer, ForeignKey("ref_disciplines.id"))
    group_id = Column(Integer, ForeignKey("ref_groups.id"))
    audience_id = Column(Integer, ForeignKey("ref_audiences.id"))
    
    day_of_week = Column(String(20), nullable=False)
    lesson_number = Column(Integer, nullable=False)
    status = Column(String(50), default="draft") # draft / published
class Teacher(Base):
    """Справочник пользователей (включая преподавателей)"""
    __tablename__ = "ref_teachers"
    id = Column(Integer, primary_key=True)
    full_name = Column(String(255), nullable=False)
    user_type_id = Column(Integer)     