from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from ..database import get_db
from ..models import Lesson, ScheduleItem, Subject
from collections import defaultdict
from datetime import date
from ..utils import apply_template_to_period

router = APIRouter(prefix="/schedule", tags=["Schedule"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/dispatcher")
def view_dispatcher_schedule(request: Request, db: Session = Depends(get_db)):
    schedules = db.query(ScheduleItem).all()
    # Группировка (пример)
    grouped_data = {}
    for s in schedules:
        key = s.lesson.groups[0].name if s.lesson and s.lesson.groups else "Без группы"
        if key not in grouped_data:
            grouped_data[key] = []
        grouped_data[key].append(s)

    return templates.TemplateResponse("dispatcher.html", {
        "request": request,
        "grouped_schedules": grouped_data  # Проверьте, что имя совпадает с тем, что в HTML
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