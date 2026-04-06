from pydantic import BaseModel
from typing import Optional

class TemplateItemResponse(BaseModel):
    id: int
    name_of_sample_id: int
    day_of_week_id: int
    time_slot_id: int
    lesson_id: int
    audience_id: int

    class Config:
        from_attributes = True

class TemplateItemCreate(BaseModel):
    name_of_sample_id: int
    day_of_week_id: int
    time_slot_id: int
    lesson_id: int
    audience_id: int

class TemplateItemUpdate(BaseModel):
    name_of_sample_id: Optional[int] = None
    day_of_week_id: Optional[int] = None
    time_slot_id: Optional[int] = None
    lesson_id: Optional[int] = None
    audience_id: Optional[int] = None