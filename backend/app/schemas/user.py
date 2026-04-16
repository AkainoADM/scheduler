from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    user_type_id: Optional[int] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    user_type_id: Optional[int] = None
    is_active: bool = True
    # password_hash: Optional[str] = None   # пока не используем

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    user_type_id: Optional[int] = None
    is_active: Optional[bool] = None
    # password_hash: Optional[str] = None