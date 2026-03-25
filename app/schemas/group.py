from pydantic import BaseModel, ConfigDict, Field, validator
from typing import Optional

class GroupResponse(BaseModel):
    id: int
    name: str
    faculty_id: int
    student_count: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class GroupCreate(BaseModel):
    name: str
    faculty_id: int
    student_count: Optional[int] = None

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    faculty_id: Optional[int] = None
    student_count: Optional[int] = None

class GroupUploadRow(BaseModel):
    name: str = Field(..., description="Название группы")
    faculty_id: int = Field(..., description="ID факультета")
    student_count: Optional[int] = Field(None, description="Количество студентов")

    @validator('student_count')
    def validate_student_count(cls, v):
        if v is not None and v < 0:
            raise ValueError('Количество студентов не может быть отрицательным')
        return v