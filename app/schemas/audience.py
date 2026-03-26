from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class AudienceResponse(BaseModel):
    id: int
    name: str
    autocreated: bool = False
    building_id: Optional[int] = None
    capacity: Optional[int] = None
    type: Optional[str] = None
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)

class AudienceCreate(BaseModel):
    name: str
    building_id: Optional[int] = None
    capacity: Optional[int] = None
    type: Optional[str] = None
    is_active: bool = True

class AudienceUpdate(BaseModel):
    name: Optional[str] = None
    building_id: Optional[int] = None
    capacity: Optional[int] = None
    type: Optional[str] = None
    is_active: Optional[bool] = None

class AudienceUploadRow(BaseModel):
    name: str = Field(..., description="Название аудитории")
    building_id: Optional[int] = Field(None, description="ID здания")
    capacity: Optional[int] = Field(None, description="Вместимость")
    type: Optional[str] = Field(None, description="Тип")
    is_active: bool = Field(True, description="Активна")