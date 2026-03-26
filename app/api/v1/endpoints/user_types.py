from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import user_type as user_type_service
from app.schemas.user_type import UserTypeCreate, UserTypeResponse, UserTypeUpdate

router = APIRouter(prefix="/user_types", tags=["User Types"])

@router.get("/", response_model=list[UserTypeResponse])
async def read_user_types(db: AsyncSession = Depends(get_db)):
    return await user_type_service.get_all_user_types(db)

@router.get("/{ut_id}", response_model=UserTypeResponse)
async def read_user_type(ut_id: int, db: AsyncSession = Depends(get_db)):
    ut = await user_type_service.get_user_type(db, ut_id)
    if not ut:
        raise HTTPException(status_code=404, detail="User type not found")
    return ut

@router.post("/", response_model=UserTypeResponse)
async def create_user_type(data: UserTypeCreate, db: AsyncSession = Depends(get_db)):
    return await user_type_service.create_user_type(db, data)

@router.put("/{ut_id}", response_model=UserTypeResponse)
async def update_user_type(ut_id: int, data: UserTypeUpdate, db: AsyncSession = Depends(get_db)):
    ut = await user_type_service.update_user_type(db, ut_id, data)
    if not ut:
        raise HTTPException(status_code=404, detail="User type not found")
    return ut

@router.delete("/{ut_id}")
async def delete_user_type(ut_id: int, db: AsyncSession = Depends(get_db)):
    await user_type_service.delete_user_type(db, ut_id)
    return {"ok": True}