from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
import datetime

class Role(Base):
    __tablename__ = "ref_roles"
    id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String, unique=True, nullable=False)

class User(Base):
    __tablename__ = "ref_users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    # Связь с ролями через таблицу op_user_roles
    roles = relationship("Role", secondary="op_user_roles")

class UserRole(Base):
    __tablename__ = "op_user_roles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("ref_users.id"))
    role_id = Column(Integer, ForeignKey("ref_roles.id"))
    expires_at = Column(DateTime, nullable=True)