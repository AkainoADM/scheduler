from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.services import subject as subject_service
from app.services import excel_import
from app.schemas.subject import SubjectCreate, SubjectResponse, SubjectUpdate

router = APIRouter(prefix="/subjects", tags=["Subjects"])

# ... все эндпоинты (GET, POST, PUT, DELETE, bulk-delete, upload)
@router.get("/", response_model=List[SubjectResponse])
async def read_subjects(db: AsyncSession = Depends(get_db)):
    return await subject_service.get_all_subjects(db)

@router.get("/{subject_id}", response_model=SubjectResponse)
async def read_subject(subject_id: int, db: AsyncSession = Depends(get_db)):
    subject = await subject_service.get_subject(db, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject

@router.post("/", response_model=SubjectResponse)
async def create_subject(data: SubjectCreate, db: AsyncSession = Depends(get_db)):
    return await subject_service.create_subject(db, data)

@router.put("/{subject_id}", response_model=SubjectResponse)
async def update_subject(subject_id: int, data: SubjectUpdate, db: AsyncSession = Depends(get_db)):
    subject = await subject_service.update_subject(db, subject_id, data)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject

@router.delete("/{subject_id}")
async def delete_subject(subject_id: int, db: AsyncSession = Depends(get_db)):
    await subject_service.delete_subject(db, subject_id)
    return {"ok": True}

@router.post("/bulk-delete")
async def bulk_delete_subjects(ids: List[int], db: AsyncSession = Depends(get_db)):
    await subject_service.bulk_delete_subjects(db, ids)
    return {"ok": True}

@router.post("/upload", summary="Загрузить дисциплины из Excel")
async def upload_subjects(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "Файл должен быть Excel (.xlsx или .xls)")
    try:
        content = await file.read()
        rows = await excel_import.parse_subjects_excel(content)
    except Exception as e:
        raise HTTPException(400, f"Ошибка чтения файла: {str(e)}")
    valid, errors = await excel_import.validate_subjects_data(rows, db)
    result = await excel_import.save_subjects_from_validated(valid, db)
    return {
        "message": "Загрузка завершена",
        "added": result["added"],
        "updated": result["updated"],
        "errors": errors
    }