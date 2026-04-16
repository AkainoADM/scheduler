from pydantic import BaseModel
from typing import Optional

class SubjectResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class SubjectCreate(BaseModel):
    name: str

class SubjectUpdate(BaseModel):
    name: Optional[str] = None