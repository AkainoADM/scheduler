import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..utils import generate_schedule
from ..models import FinalScheduleItem, ScheduleItem
from datetime import date, timedelta
from datetime import datetime

router = APIRouter(prefix="/api", tags=["API"])

@router.post("/generate")
@router.post("/generate")
def run_generation(
    start_date: str, 
    end_date: str, 
    db: Session = Depends(get_db)
):
    try:
        # Теперь datetime.strptime сработает корректно
        date_start = datetime.strptime(start_date, "%d.%m.%Y").date()
        date_end = datetime.strptime(end_date, "%d.%m.%Y").date()
        
        # Проверка: дата начала не может быть позже даты конца
        if date_start > date_end:
            raise HTTPException(status_code=400, detail="Дата начала не может быть позже даты окончания")
            
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail="Неверный формат даты. Используйте ДД.ММ.ГГГГ (например, 12.03.2026)"
        )
    
    # Вызываем генерацию с объектами date
    result = generate_schedule(db, date_start, date_end)
    return result
@router.get("/schedule")
def get_schedule(db: Session = Depends(get_db)):
    items = db.query(ScheduleItem).all()
    
    schedule_data = []
    for item in items:
        lesson = item.lesson
        subject = lesson.subject if lesson else None
        teacher_name = "Не назначен"
        
        if subject and subject.teachers:
            teacher_name = ", ".join([t.name for t in subject.teachers])
            
        schedule_data.append({
            "subject": subject.name if subject else "---", 
            "teacher": teacher_name,
            "audience": item.audience.name if item.audience else "---", 
            "date": str(item.date) if item.date is not None else "---", 
            "pair": item.time_slot.slot_number if item.time_slot else None,
            "time": f"{item.time_slot.start_time} - {item.time_slot.end_time}" if item.time_slot else "---"
        })
    
    return schedule_data
# Добавь эти эндпоинты в api.py

@router.post("/schedule/pin/{item_id}")
def pin_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(ScheduleItem).filter(ScheduleItem.id == item_id).first()
    if not item:
        return {"status": "error", "message": "Запись не найдена"}
    
    # Переключаем статус (был True станет False и наоборот)
    item.is_pinned = not item.is_pinned
    db.commit()
    return {"is_pinned": item.is_pinned}

@router.post("/schedule/approve")
def approve_schedule(db: Session = Depends(get_db)):
    from ..models import FinalScheduleItem
    # 1. Очищаем старый чистовик
    db.query(FinalScheduleItem).delete()
    
    # 2. Копируем всё из черновика
    drafts = db.query(ScheduleItem).all()
    for d in drafts:
        final = FinalScheduleItem(
            lesson_id=d.lesson_id,
            time_slot_id=d.time_slot_id,
            audience_id=d.audience_id,
            date=d.date
        )
        db.add(final)
    
    db.commit()
    return {"status": "success"}

