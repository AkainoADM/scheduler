from pydantic import BaseModel
from typing import Optional

class TemplateNameResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class TemplateNameCreate(BaseModel):
    name: str

class TemplateNameUpdate(BaseModel):
    name: Optional[str] = None