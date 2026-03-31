from sched import scheduler
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from ..database import get_db
from ..models import Lesson, ScheduleItem
from itertools import groupby
from collections import defaultdict
router = APIRouter(prefix="/schedule", tags=["Schedule"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/dispatcher")
def view_dispatcher_schedule(request: Request, db: Session = Depends(get_db)):
    # 1. Получаем отсортированные данные
    schedules = db.query(ScheduleItem).options(
        joinedload(ScheduleItem.lesson).joinedload(Lesson.groups),
        joinedload(ScheduleItem.lesson).joinedload(Lesson.teachers),
        joinedload(ScheduleItem.time_slot),
        joinedload(ScheduleItem.audience)
    ).order_by(ScheduleItem.date, ScheduleItem.time_slot_id).all()

    # 2. Группируем в Python (сохраняя порядок сортировки)
    grouped_data = defaultdict(list)
    for item in schedules:
        # Используем дату и имя слота как ключ для группировки
        key = (item.date, item.time_slot.name)
        grouped_data[key].append(item)

    # 3. Передаем в шаблон .items() (это список кортежей [((дата, слот), [items...]), ...])
    return templates.TemplateResponse("dispatcher.html", {
        "request": request, 
        "grouped_schedules": grouped_data.items()
    })