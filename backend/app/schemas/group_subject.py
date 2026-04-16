from pydantic import BaseModel

class GroupSubjectResponse(BaseModel):
    group_id: int
    subject_id: int

    class Config:
        from_attributes = True

class GroupSubjectCreate(BaseModel):
    group_id: int
    subject_id: int