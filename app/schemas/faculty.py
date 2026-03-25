from pydantic import BaseModel, ConfigDict
from typing import Optional

class FacultyResponse(BaseModel):
    id: int
    name: str
    display_name: Optional[str] = None
    short_display_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)