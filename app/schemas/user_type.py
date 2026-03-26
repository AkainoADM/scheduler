from pydantic import BaseModel, ConfigDict
from typing import Optional

class UserTypeResponse(BaseModel):
    id: int
    code: str
    name: Optional[str] = None
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class UserTypeCreate(BaseModel):
    code: str
    name: Optional[str] = None
    description: Optional[str] = None

class UserTypeUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None