from pydantic import BaseModel, ConfigDict
from typing import Optional

class SubdivisionResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)

class SubdivisionCreate(BaseModel):
    name: str

class SubdivisionUpdate(BaseModel):
    name: Optional[str] = None