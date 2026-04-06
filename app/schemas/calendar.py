from pydantic import BaseModel
from datetime import date as date_type
from typing import Optional

class CalendarResponse(BaseModel):
    id: int
    date: date_type
    is_working_day: bool
    week_type: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True

class CalendarCreate(BaseModel):
    date: date_type
    is_working_day: bool = True
    week_type: Optional[str] = None
    description: Optional[str] = None

class CalendarUpdate(BaseModel):
    date: Optional[date_type] = None
    is_working_day: Optional[bool] = None
    week_type: Optional[str] = None
    description: Optional[str] = None