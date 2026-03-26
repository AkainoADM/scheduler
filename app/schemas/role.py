from pydantic import BaseModel, ConfigDict
from typing import Optional

class RoleResponse(BaseModel):
    id: int
    role_name: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class RoleCreate(BaseModel):
    role_name: str
    description: Optional[str] = None

class RoleUpdate(BaseModel):
    role_name: Optional[str] = None
    description: Optional[str] = None