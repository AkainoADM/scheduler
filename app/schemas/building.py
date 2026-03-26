from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class BuildingResponse(BaseModel):
    id: int
    name: str
    address: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class BuildingCreate(BaseModel):
    name: str
    address: Optional[str] = None

class BuildingUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None

class BuildingUploadRow(BaseModel):
    name: str = Field(..., description="Название здания")
    address: Optional[str] = Field(None, description="Адрес")