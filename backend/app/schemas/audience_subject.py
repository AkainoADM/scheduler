from pydantic import BaseModel

class AudienceSubjectResponse(BaseModel):
    audience_id: int
    subject_id: int

    class Config:
        from_attributes = True

class AudienceSubjectCreate(BaseModel):
    audience_id: int
    subject_id: int