from pydantic import BaseModel
from typing import Optional

class TeacherSubjectResponse(BaseModel):
    teacher_id: int
    subject_id: int
    is_main: bool = False

    class Config:
        from_attributes = True

class TeacherSubjectCreate(BaseModel):
    teacher_id: int
    subject_id: int
    is_main: bool = False

class TeacherSubjectUpdate(BaseModel):
    is_main: Optional[bool] = None