from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import ScheduleItem

router = APIRouter(prefix="/schedule", tags=["Schedule"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/dispatcher", response_class=HTMLResponse)
def view_dispatcher_schedule(request: Request, db: Session = Depends(get_db)):
    items = db.query(ScheduleItem).all()
    
    schedule_data = {}
    
    for item in items:
        lesson = item.lesson
        slot_name = item.time_slot.name if item.time_slot else f"Пара {item.time_slot_id}"
        date_str = str(item.date) if item.date is not None else "Неизвестная дата"
        teachers_str = ", ".join([t.name for t in lesson.teachers]) if lesson.teachers else "Не назначен"
        groups_str = ", ".join([g.name for g in lesson.groups]) if lesson.groups else "Нет группы"
        audience_str = item.audience.name if item.audience else "---"

        if date_str not in schedule_data:
            schedule_data[date_str] = {}
            
        if slot_name not in schedule_data[date_str]:
            schedule_data[date_str][slot_name] = []

        schedule_data[date_str][slot_name].append({
            "subject": lesson.subject if lesson else "---",
            "group": groups_str,
            "audience": audience_str,
            "teacher": teachers_str,
            "type": lesson.type if lesson else ""
        })

    return templates.TemplateResponse("dispatcher.html", {
        "request": request,
        "schedule_dict": schedule_data
    })
