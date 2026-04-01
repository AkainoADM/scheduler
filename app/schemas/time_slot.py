from pydantic import BaseModel
from datetime import time
from typing import Optional

class TimeSlotResponse(BaseModel):
    id: int
    slot_number: int
    name: str
    start_time: time
    end_time: time
    duration_minutes: Optional[int] = None
    break_after_minutes: Optional[int] = None
    is_active: bool = True

    class Config:
        from_attributes = True

class TimeSlotCreate(BaseModel):
    slot_number: int
    name: str
    start_time: time
    end_time: time
    duration_minutes: Optional[int] = None
    break_after_minutes: Optional[int] = None
    is_active: bool = True

class TimeSlotUpdate(BaseModel):
    slot_number: Optional[int] = None
    name: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    duration_minutes: Optional[int] = None
    break_after_minutes: Optional[int] = None
    is_active: Optional[bool] = None