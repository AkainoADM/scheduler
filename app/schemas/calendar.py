from pydantic import BaseModel
import datetime
from typing import Optional

class CalendarResponse(BaseModel):
    id: int
    date: datetime.date
    is_working_day: bool
    week_type: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True

class CalendarCreate(BaseModel):
    date: datetime.date
    is_working_day: bool = True
    week_type: Optional[str] = None
    description: Optional[str] = None

class CalendarUpdate(BaseModel):
    date: Optional[datetime.date] = None
    is_working_day: Optional[bool] = None
    week_type: Optional[str] = None
    description: Optional[str] = None