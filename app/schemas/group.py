from pydantic import BaseModel
from typing import Optional

class GroupResponse(BaseModel):
    id: int
    name: str
    faculty_id: Optional[int] = None
    student_count: Optional[int] = None

    class Config:
        from_attributes = True

class GroupCreate(BaseModel):
    name: str
    faculty_id: Optional[int] = None
    student_count: Optional[int] = None

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    faculty_id: Optional[int] = None
    student_count: Optional[int] = None