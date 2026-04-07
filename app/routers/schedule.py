import datetime
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload, selectinload
from ..database import get_db
from ..models import Lesson, ScheduleItem, Subject, TemplateItem
from collections import defaultdict
from datetime import date, timedelta
from ..utils import apply_template_to_period
router = APIRouter(prefix="/schedule", tags=["Schedule"])
templates = Jinja2Templates(directory="app/templates")
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import ScheduleItem, Teacher, Subject, Group

@router.get("/dispatcher")
def view_dispatcher_schedule(request: Request, db: Session = Depends(get_db)):
    # Получаем сырые данные
    items = db.query(ScheduleItem).all()
    
    print("\n--- ПРОВЕРКА ДАННЫХ В БАЗЕ ---")
    if not items:
        print("В таблице op_schedule_items ПУСТО")
    else:
        for i in items[:5]: # Посмотрим первые 5 записей
            print(f"ID: {i.id} | Дата: {i.date} | LessonID: {i.lesson_id}")
    print("------------------------------\n")

    # Группируем для шаблона
    grouped_data = {}
    for item in items:
        # Упрощенный ключ для теста
        key = "Все занятия" 
        if key not in grouped_data:
            grouped_data[key] = []
        grouped_data[key].append(item)

    return templates.TemplateResponse("dispatcher.html", {
        "request": request,
        "grouped_schedules": grouped_data
    })
@router.post("/apply-template")
def run_template_application(
    sample_id: int, 
    start_date: date, 
    end_date: date, 
    db: Session = Depends(get_db)
):
    try:
        count = apply_template_to_period(db, sample_id, start_date, end_date)
        return {"status": "success", "created_items": count}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))