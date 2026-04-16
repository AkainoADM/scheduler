from pydantic import BaseModel
from typing import Optional

class DayOfWeekResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class DayOfWeekCreate(BaseModel):
    name: str

class DayOfWeekUpdate(BaseModel):
    name: Optional[str] = None