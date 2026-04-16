from pydantic import BaseModel

class TeacherGroupResponse(BaseModel):
    teacher_id: int
    group_id: int

    class Config:
        from_attributes = True

class TeacherGroupCreate(BaseModel):
    teacher_id: int
    group_id: int