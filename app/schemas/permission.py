from pydantic import BaseModel
from typing import Optional

class PermissionResponse(BaseModel):
    id: int
    permission_code: str
    permission_name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class PermissionCreate(BaseModel):
    permission_code: str
    permission_name: str
    description: Optional[str] = None

class PermissionUpdate(BaseModel):
    permission_code: Optional[str] = None
    permission_name: Optional[str] = None
    description: Optional[str] = None