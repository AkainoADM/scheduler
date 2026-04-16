from pydantic import BaseModel
from typing import Optional

class UserTypeResponse(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class UserTypeCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None

class UserTypeUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None