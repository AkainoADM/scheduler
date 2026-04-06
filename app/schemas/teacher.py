from pydantic import BaseModel
from typing import Optional

class TeacherResponse(BaseModel):
    id: int
    login: str
    name: str
    url: Optional[str] = None

    class Config:
        from_attributes = True

class TeacherCreate(BaseModel):
    login: str
    name: str
    url: Optional[str] = None

class TeacherUpdate(BaseModel):
    login: Optional[str] = None
    name: Optional[str] = None
    url: Optional[str] = None