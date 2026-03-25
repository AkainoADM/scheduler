from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import faculty as service
from pydantic import BaseModel

class FacultyResponse(BaseModel):
    id: int
    name: str

router = APIRouter(prefix="/faculties", tags=["Faculties"])

@router.get("/", response_model=list[FacultyResponse])
async def read_faculties(db: AsyncSession = Depends(get_db)):
    faculties = await service.get_all_faculties(db)
    return [{"id": f.id, "name": f.name} for f in faculties]