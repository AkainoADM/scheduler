# backend/app/api/routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from app.api.deps import get_db
from app import models
from app.config import settings
from datetime import datetime
from app.generator import generate_schedule
from app.schemas import GeneratePayload
router = APIRouter(prefix="/api")

@router.post("/schedule/generate")
def api_generat(payload: GeneratePayload):
    return generate_schedule(payload.group_ids, payload.start_date, payload.end_date, options=payload.options)

@router.get("/groups")
def list_groups(db=Depends(get_db)):
    groups = db.query(models.RefGroup).all()
    return [{"id": g.id, "name": g.name} for g in groups]

@router.post("/schedule/generate")
def api_generate(payload: dict):
    group_ids = payload.get("group_ids", [])
    start = payload.get("start_date")
    end = payload.get("end_date")
    if not group_ids or not start or not end:
        raise HTTPException(status_code=400, detail="group_ids, start_date, end_date required")
    from app.generator import generate_schedule
    return generate_schedule(group_ids, start, end, options=payload.get("options"))

@router.get("/schedule/structured")
def get_structured(group_id: int, start: str, end: str, db=Depends(get_db)):
    start_date = datetime.strptime(start, settings.DATE_FORMAT).date()
    end_date = datetime.strptime(end, settings.DATE_FORMAT).date()
    # Получаем schedule items для группы (предполагается связь lesson->group в вашей модели; если нет — адаптируйте)
    rows = db.query(models.OpScheduleItem).filter(models.OpScheduleItem.date >= start_date, models.OpScheduleItem.date <= end_date).all()
    out = {"group_id": group_id, "group_name": None, "dates": []}
    group = db.get(models.RefGroup, group_id)
    if group:
        out["group_name"] = group.name
    # агрегируем
    temp = {}
    for item in rows:
        lesson = db.get(models.OpLesson, item.lesson_id)
        if lesson is None:
            continue
        date_str = lesson.date.strftime(settings.DATE_FORMAT)
        temp.setdefault(date_str, []).append({
            "slot": item.time_slot_id,
            "subject_id": lesson.subject_id,
            "lesson_id": lesson.id,
            "audience_id": item.audience_id,
            "status": item.status
        })
    for d, pairs in temp.items():
        pairs_sorted = sorted(pairs, key=lambda x: x["slot"])
        out["dates"].append({"date": d, "pairs": pairs_sorted})
    return out
