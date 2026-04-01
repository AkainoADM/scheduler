from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..utils import generate_schedule
from ..models import ScheduleItem

router = APIRouter(prefix="/api", tags=["API"])

@router.post("/generate")
def generate(db: Session = Depends(get_db)):
    count = generate_schedule(db)
    if count.get("count", 0) == 0:
        return {"status": "error", "message": "Недостаточно данных"}
    return count

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