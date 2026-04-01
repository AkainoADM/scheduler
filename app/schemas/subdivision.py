from pydantic import BaseModel
from typing import Optional

class SubdivisionResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class SubdivisionCreate(BaseModel):
    name: str

class SubdivisionUpdate(BaseModel):
    name: Optional[str] = None