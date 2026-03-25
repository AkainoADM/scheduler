from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db
from ..models import Discipline, Group, Audience, User, Timetable
from ..utils import generate_schedule
router = APIRouter(prefix="/api", tags=["API"])


@router.post("/generate")
def generate_schedule(db: Session = Depends(get_db)):
    lessons = db.query(Discipline).all()
    groups = db.query(Group).all()
    audiences = db.query(Audience).all()

    if not lessons or not groups or not audiences:
        raise HTTPException(status_code=400, detail="Справочники пусты.")
    
    count = generate_schedule(db, lessons, groups, audiences)
    return {"status": "success", "count": count}
@router.get("/db-check")
def check_db_connection(db: Session = Depends(get_db)):
    try:
        # Проверяем реальное наличие базы 'raspisanie' 
        db.execute(text("SELECT 1"))
        # Считаем учителей из таблицы ref_users 
        t_count = db.query(User).count() 
        return {"status": "success", "teachers_in_db": t_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка БД: {str(e)}")
    

@router.post("/generate")
def get_schedule(db: Session = Depends(get_db)):
    # Получаем все элементы расписания из op_schedule_items [cite: 157]
    items = db.query(Timetable).all()
    users_dict = {u.id: u.full_name for u in db.query(User).all()}
    lessons_dict = {l.id: l for l in db.query(Discipline).all()}
    
    schedule_data = []
    for item in items:
        lsn = lessons_dict.get(item.discipline_id)
        teacher_name = "Не назначен"
        if lsn and lsn.teacher_id:  # type: ignore
            teacher_name = users_dict.get(lsn.teacher_id, "Неизвестный ID")
            
        schedule_data.append({
            "subject": lsn.name if lsn else "---",
            "teacher": teacher_name,
            "audience": item.audience_id, # ref_audiences [cite: 171]
            "day": item.day_of_week,
            "pair": item.lesson_number
        })
    
    return schedule_data

