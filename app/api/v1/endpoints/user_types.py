from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import user_type as service
from app.schemas.user_type import UserTypeCreate, UserTypeResponse, UserTypeUpdate
from typing import List

router = APIRouter(prefix="/user-types", tags=["UserTypes"])

@router.get("/", response_model=list[UserTypeResponse])
async def read_user_types(db: AsyncSession = Depends(get_db)):
    return await service.get_all_user_types(db)

@router.get("/{ut_id}", response_model=UserTypeResponse)
async def read_user_type(ut_id: int, db: AsyncSession = Depends(get_db)):
    ut = await service.get_user_type(db, ut_id)
    if not ut:
        raise HTTPException(status_code=404, detail="UserType not found")
    return ut

@router.post("/", response_model=UserTypeResponse)
async def create_user_type(data: UserTypeCreate, db: AsyncSession = Depends(get_db)):
    return await service.create_user_type(db, data)

@router.put("/{ut_id}", response_model=UserTypeResponse)
async def update_user_type(ut_id: int, data: UserTypeUpdate, db: AsyncSession = Depends(get_db)):
    ut = await service.update_user_type(db, ut_id, data)
    if not ut:
        raise HTTPException(status_code=404, detail="UserType not found")
    return ut

@router.delete("/{ut_id}")
async def delete_user_type(ut_id: int, db: AsyncSession = Depends(get_db)):
    await service.delete_user_type(db, ut_id)
    return {"ok": True}

@router.post("/bulk-delete")
async def bulk_delete_user_types(ids: List[int], db: AsyncSession = Depends(get_db)):
    await service.bulk_delete_user_types(db, ids)
    return {"ok": True}

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.services import user_type as user_type_service
from app.services import excel_import
from app.schemas.user_type import UserTypeCreate, UserTypeResponse, UserTypeUpdate

router = APIRouter(prefix="/user-types", tags=["User Types"])

@router.get("/", response_model=List[UserTypeResponse])
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

@router.post("/bulk-delete")
async def bulk_delete_user_types(ids: List[int], db: AsyncSession = Depends(get_db)):
    await user_type_service.bulk_delete_user_types(db, ids)
    return {"ok": True}

@router.post("/upload", summary="Загрузить типы пользователей из Excel")
async def upload_user_types(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "Файл должен быть Excel (.xlsx или .xls)")
    try:
        content = await file.read()
        rows = await excel_import.parse_user_types_excel(content)
    except Exception as e:
        raise HTTPException(400, f"Ошибка чтения файла: {str(e)}")
    valid, errors = await excel_import.validate_user_types_data(rows, db)
    result = await excel_import.save_user_types_from_validated(valid, db)
    return {
        "message": "Загрузка завершена",
        "added": result["added"],
        "updated": result["updated"],
        "errors": errors
    }