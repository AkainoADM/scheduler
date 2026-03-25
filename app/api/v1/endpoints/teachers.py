from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import teacher as teacher_service
from app.schemas.teacher import TeacherCreate, TeacherResponse, TeacherUpdate
from app.services.excel_import import parse_teachers_excel, validate_teachers_data, save_teachers_from_validated

router = APIRouter(prefix="/teachers", tags=["Teachers"])

@router.get("/", response_model=list[TeacherResponse])
async def read_teachers(db: AsyncSession = Depends(get_db)):
    return await teacher_service.get_all_teachers(db)

@router.get("/{teacher_id}", response_model=TeacherResponse)
async def read_teacher(teacher_id: int, db: AsyncSession = Depends(get_db)):
    teacher = await teacher_service.get_teacher(db, teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return teacher

@router.post("/", response_model=TeacherResponse)
async def create_teacher(data: TeacherCreate, db: AsyncSession = Depends(get_db)):
    return await teacher_service.create_teacher(db, data)

@router.put("/{teacher_id}", response_model=TeacherResponse)
async def update_teacher(teacher_id: int, data: TeacherUpdate, db: AsyncSession = Depends(get_db)):
    teacher = await teacher_service.update_teacher(db, teacher_id, data)
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return teacher

@router.delete("/{teacher_id}")
async def delete_teacher(teacher_id: int, db: AsyncSession = Depends(get_db)):
    await teacher_service.delete_teacher(db, teacher_id)
    return {"ok": True}

@router.post("/upload", summary="Загрузить преподавателей из Excel")
async def upload_teachers(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "Файл должен быть Excel (.xlsx или .xls)")
    try:
        content = await file.read()
        rows = await parse_teachers_excel(content)
    except Exception as e:
        raise HTTPException(400, f"Ошибка чтения файла: {str(e)}")

    valid_rows, errors = await validate_teachers_data(rows, db)
    result = await save_teachers_from_validated(valid_rows, db)

    return {
        "message": "Загрузка завершена",
        "added": result["added"],
        "updated": result["updated"],
        "errors": errors
    }