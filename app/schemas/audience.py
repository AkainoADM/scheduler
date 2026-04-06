from pydantic import BaseModel
from typing import Optional

class AudienceResponse(BaseModel):
    id: int
    name: str
    building_id: Optional[int] = None
    capacity: Optional[int] = None
    type: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True

class AudienceCreate(BaseModel):
    name: str
    building_id: Optional[int] = None
    capacity: Optional[int] = None
    type: Optional[str] = None
    is_active: bool = True

class AudienceUpdate(BaseModel):
    name: Optional[str] = None
    building_id: Optional[int] = None
    capacity: Optional[int] = None
    type: Optional[str] = None
    is_active: Optional[bool] = None