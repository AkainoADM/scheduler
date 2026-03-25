from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..utils import generate_schedule
from ..models import ScheduleItem
router = APIRouter(prefix="/api", tags=["API"])

@router.post("/generate")
def generate(db: Session = Depends(get_db)):
    count = generate_schedule(db)
    if count == 0:
        return {"status": "error", "message": "Недостаточно данных (проверьте op_lessons, ref_time_slots, ref_audiences)"}
    return {"status": "success", "count": count}
@router.get("/schedule")
def get_schedule(db: Session = Depends(get_db)):
    items = db.query(ScheduleItem).all()
    
    schedule_data = []
    for item in items:
        lesson = item.lesson
        teacher_name = "Не назначен"
        if lesson and lesson.teachers:
            teacher_name = ", ".join([t.name for t in lesson.teachers])
            
        schedule_data.append({
            "subject": lesson.subject if lesson else "---", 
            "teacher": teacher_name,
            "audience": item.audience.name if item.audience else "---", 
            "date": str(item.date) if item.date is not None else "---", 
            "pair": item.time_slot.slot_number if item.time_slot else None,
            "time": f"{item.time_slot.start_time} - {item.time_slot.end_time}" if item.time_slot else "---"
        })
    
    return schedule_data
