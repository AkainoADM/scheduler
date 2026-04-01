from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from ..database import get_db
from ..models import Lesson, ScheduleItem, Subject
from collections import defaultdict

router = APIRouter(prefix="/schedule", tags=["Schedule"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/dispatcher")
def view_dispatcher_schedule(request: Request, db: Session = Depends(get_db)):
    # Подгружаем все данные
    schedules = db.query(ScheduleItem).options(
        joinedload(ScheduleItem.lesson).joinedload(Lesson.subject).joinedload(Subject.groups),
        joinedload(ScheduleItem.lesson).joinedload(Lesson.subject).joinedload(Subject.teachers),
        joinedload(ScheduleItem.time_slot),
        joinedload(ScheduleItem.audience)
    ).all()

    # Группируем расписание ПО ГРУППАМ
    grouped_by_group = defaultdict(list)
    
    for item in schedules:
        if item.lesson and item.lesson.subject and item.lesson.subject.groups:
            # Если у пары несколько групп, она добавится в расписание каждой!
            for group in item.lesson.subject.groups:
                grouped_by_group[group.name].append(item)

    # Сортируем пары внутри каждой группы по Дате и Времени (номеру пары)
    for group_name in grouped_by_group:
        grouped_by_group[group_name].sort(key=lambda x: (x.date, x.time_slot.slot_number))

    # Сортируем сами группы по алфавиту/номеру (чтобы 130Б шла перед 136Б)
    grouped_data = dict(sorted(grouped_by_group.items()))

    return templates.TemplateResponse("dispatcher.html", {
        "request": request, 
        "grouped_schedules": grouped_data
    })