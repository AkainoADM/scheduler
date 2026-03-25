from pydantic import BaseModel, ConfigDict
from typing import Optional

class TeacherResponse(BaseModel):
    id: int
    login: str
    name: str
    url: Optional[str] = None
    max_hours_per_day: Optional[int] = None
    max_hours_per_week: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class TeacherCreate(BaseModel):
    login: str
    name: str
    url: Optional[str] = None
    max_hours_per_day: Optional[int] = None
    max_hours_per_week: Optional[int] = None

class TeacherUpdate(BaseModel):
    login: Optional[str] = None
    name: Optional[str] = None
    url: Optional[str] = None
    max_hours_per_day: Optional[int] = None
    max_hours_per_week: Optional[int] = None

    class TeacherUploadRow(BaseModel):
    login: str = Field(..., description="Логин")
    name: str = Field(..., description="ФИО")
    url: Optional[str] = Field(None, description="Ссылка")
    max_hours_per_day: Optional[int] = Field(None, description="Макс. часов в день")
    max_hours_per_week: Optional[int] = Field(None, description="Макс. часов в неделю")

