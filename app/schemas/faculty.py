from pydantic import BaseModel, ConfigDict
from typing import Optional

class FacultyResponse(BaseModel):
    id: int
    name: str
    display_name: Optional[str] = None
    short_display_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class FacultyCreate(BaseModel):
    name: str
    display_name: Optional[str] = None
    short_display_name: Optional[str] = None

class FacultyUpdate(BaseModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    short_display_name: Optional[str] = None