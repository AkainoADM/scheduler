from pydantic import BaseModel
from typing import Optional

class BuildingResponse(BaseModel):
    id: int
    name: str
    address: Optional[str] = None

    class Config:
        from_attributes = True

class BuildingCreate(BaseModel):
    name: str
    address: Optional[str] = None

class BuildingUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None