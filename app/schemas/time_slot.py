from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import time

class TimeSlotResponse(BaseModel):
    id: int
    slot_number: Optional[int] = None
    name: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    duration_minutes: Optional[int] = None
    break_after_minutes: Optional[int] = None
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)

class TimeSlotCreate(BaseModel):
    slot_number: Optional[int] = None
    name: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
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