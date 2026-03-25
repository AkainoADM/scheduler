from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey, Time, Date, DateTime,
    JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.core.database import Base

# ===============================
# 1. Справочные таблицы (ref_*)
# ===============================

class UserType(Base):
    __tablename__ = "ref_user_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String)
    description = Column(String)


class Subdivision(Base):
    __tablename__ = "ref_subdivisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)


class Building(Base):
    __tablename__ = "ref_buildings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    address = Column(String)


class Audience(Base):
    __tablename__ = "ref_audiences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    autocreated = Column(Boolean)
    building_id = Column(Integer, ForeignKey("ref_buildings.id"))
    capacity = Column(Integer)
    type = Column(String)          # "лекционная", "практическая", "лабораторная", "компьютерный класс"
    is_active = Column(Boolean)

    building = relationship("Building", backref="audiences")


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
    faculty_id = Column(Integer, ForeignKey("ref_faculties.id"))
    student_count = Column(Integer)

    faculty = relationship("Faculty", backref="groups")


class Teacher(Base):
    __tablename__ = "ref_teachers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    login = Column(String, unique=True)
    name = Column(String)
    url = Column(String)
    max_hours_per_day = Column(Integer)
    max_hours_per_week = Column(Integer)


class TimeSlot(Base):
    __tablename__ = "ref_time_slots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slot_number = Column(Integer)
    name = Column(String)
    start_time = Column(Time)
    end_time = Column(Time)
    duration_minutes = Column(Integer)
    break_after_minutes = Column(Integer)
    is_active = Column(Boolean)


class User(Base):
    __tablename__ = "ref_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    password_hash = Column(String)
    full_name = Column(String)
    user_type_id = Column(Integer, ForeignKey("ref_user_types.id"))
    is_active = Column(Boolean)
    created_at = Column(DateTime)
    last_login = Column(DateTime)

    user_type = relationship("UserType")


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


# ===============================
# 2. Операционные таблицы (op_*)
# ===============================

class AudienceSubdivision(Base):
    __tablename__ = "op_audiences_of_subdivisions"

    audience_id = Column(Integer, ForeignKey("ref_audiences.id"), primary_key=True)
    subdivision_id = Column(Integer, ForeignKey("ref_subdivisions.id"), primary_key=True)


class Insertion(Base):
    __tablename__ = "op_insertions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime)
    faculty_id = Column(Integer, ForeignKey("ref_faculties.id"))
    hash = Column(String)
    status = Column(String)

    faculty = relationship("Faculty")


class Lesson(Base):
    __tablename__ = "op_lessons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String)
    date = Column(Date)
    subject = Column(String)
    insertion_id = Column(Integer, ForeignKey("op_insertions.id"))
    time_slot_id = Column(Integer, ForeignKey("ref_time_slots.id"))
    week_day = Column(Integer)
    type = Column(String)
    student_count = Column(Integer)

    insertion = relationship("Insertion", backref="lessons")
    time_slot = relationship("TimeSlot")


class AudienceOfPair(Base):
    __tablename__ = "op_audiences_of_pairs"

    audience_id = Column(Integer, ForeignKey("ref_audiences.id"), primary_key=True)
    lesson_id = Column(Integer, ForeignKey("op_lessons.id"), primary_key=True)

    audience = relationship("Audience")
    lesson = relationship("Lesson")


class GroupOfPair(Base):
    __tablename__ = "op_groups_of_pairs"

    group_id = Column(Integer, ForeignKey("ref_groups.id"), primary_key=True)
    lesson_id = Column(Integer, ForeignKey("op_lessons.id"), primary_key=True)

    group = relationship("Group")
    lesson = relationship("Lesson")


class TeacherOfPair(Base):
    __tablename__ = "op_teachers_of_pairs"

    teacher_id = Column(Integer, ForeignKey("ref_teachers.id"), primary_key=True)
    lesson_id = Column(Integer, ForeignKey("op_lessons.id"), primary_key=True)
    is_main = Column(Boolean)

    teacher = relationship("Teacher")
    lesson = relationship("Lesson")


class TeacherWorkWindow(Base):
    __tablename__ = "op_teacher_work_windows"

    id = Column(Integer, primary_key=True, autoincrement=True)
    teacher_id = Column(Integer, ForeignKey("ref_teachers.id"))
    day_of_week = Column(Integer)          # 1–7
    start_time = Column(Time)
    end_time = Column(Time)
    is_available = Column(Boolean)

    teacher = relationship("Teacher", backref="work_windows")


class ScheduleItem(Base):
    __tablename__ = "op_schedule_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lesson_id = Column(Integer, ForeignKey("op_lessons.id"))
    time_slot_id = Column(Integer, ForeignKey("ref_time_slots.id"))
    audience_id = Column(Integer, ForeignKey("ref_audiences.id"))
    date = Column(Date)
    status = Column(String)          # например, "published", "draft"

    lesson = relationship("Lesson")
    time_slot = relationship("TimeSlot")
    audience = relationship("Audience")


class UserRole(Base):
    __tablename__ = "op_user_roles"

    user_id = Column(Integer, ForeignKey("ref_users.id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("ref_roles.id"), primary_key=True)
    assigned_by = Column(Integer, ForeignKey("ref_users.id"))
    assigned_at = Column(DateTime)
    expires_at = Column(DateTime)

    user = relationship("User", foreign_keys=[user_id])
    role = relationship("Role")
    assigner = relationship("User", foreign_keys=[assigned_by])


class RolePermission(Base):
    __tablename__ = "op_role_permissions"

    role_id = Column(Integer, ForeignKey("ref_roles.id"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("ref_permissions.id"), primary_key=True)
    granted_by = Column(Integer, ForeignKey("ref_users.id"))
    granted_at = Column(DateTime)

    role = relationship("Role")
    permission = relationship("Permission")
    granter = relationship("User", foreign_keys=[granted_by])


class TeacherUser(Base):
    __tablename__ = "op_teacher_users"

    teacher_id = Column(Integer, ForeignKey("ref_teachers.id"), primary_key=True, unique=True)
    user_id = Column(Integer, ForeignKey("ref_users.id"), primary_key=True, unique=True)
    is_primary = Column(Boolean)

    teacher = relationship("Teacher")
    user = relationship("User")


class UserActivityLog(Base):
    __tablename__ = "op_user_activity_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("ref_users.id"))
    action_type = Column(String)
    action_details = Column(JSON)
    ip_address = Column(String)
    user_agent = Column(String)
    created_at = Column(DateTime)

    user = relationship("User", backref="activity_logs")


class UserFaculty(Base):
    __tablename__ = "op_user_faculties"

    user_id = Column(Integer, ForeignKey("ref_users.id"), primary_key=True)
    faculty_id = Column(Integer, ForeignKey("ref_faculties.id"), primary_key=True)
    access_level = Column(String)

    user = relationship("User")
    faculty = relationship("Faculty")