import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Lesson, ScheduleItem, TemplateItem
from datetime import date, timedelta
from datetime import datetime

router = APIRouter(prefix="/api", tags=["API"])

@router.post("/generate")
def run_generation(start_date: str, end_date: str, db: Session = Depends(get_db)):
    print("\n" + "="*40)
    print("🚀 ЗАПУСК ГЕНЕРАЦИИ")
    
    try:
        start_dt = datetime.strptime(start_date, "%d.%m.%Y").date()
        end_dt = datetime.strptime(end_date, "%d.%m.%Y").date()
        print(f"📅 Период: {start_dt} ---> {end_dt}")
        
        if start_dt > end_dt:
            return {"status": "error", "message": "Wrong date range"}
    except ValueError:
        raise HTTPException(status_code=422, detail="Формат даты должен быть ДД.ММ.ГГГГ")

    all_templates = db.query(TemplateItem).all()
    if not all_templates:
        return {"status": "ok", "count": 0, "msg": "No templates found"}

    current_date = start_dt
    created_count = 0

    while current_date <= end_dt:
        day_of_week = current_date.weekday() + 1 
        daily_items = [ti for ti in all_templates if ti.day_of_week_id == day_of_week]

        for ti in daily_items:
            # --- ШАГ 1: Создаем реальный УРОК (Lesson) на эту дату ---
            # Раньше ты этого не делал, поэтому база ругалась на пустой ID
            new_lesson = Lesson(
                subject_id=ti.subject_id, # Берем предмет из шаблона
                date=current_date,
                student_count=0
            )
            db.add(new_lesson)
            
            # Нам нужен ID этого урока прямо сейчас для следующего шага
            db.flush() 

            # --- ШАГ 2: Создаем запись в РАСПИСАНИИ (ScheduleItem) ---
            new_item = ScheduleItem(
                date=current_date,
                lesson_id=new_lesson.id,  # ПЕРЕДАЕМ ID ТОЛЬКО ЧТО СОЗДАННОГО УРОКА
                time_slot_id=ti.time_slot_id,
                audience_id=ti.audience_id,
                status="scheduled",
                is_pinned=True
            )
            db.add(new_item)
            created_count += 1
            print(f"   ✅ Создан урок {new_lesson.id} (Предмет {ti.subject_id}) в слот {ti.time_slot_id}")

        current_date += timedelta(days=1)

    print(f"💾 Сохраняю изменения в БД...")
    db.commit()
    print("✨ ГЕНЕРАЦИЯ ЗАВЕРШЕНА")
    print("="*40 + "\n")

    return {"status": "success", "generated_count": created_count}

# Остальные методы (get_schedule, pin_item, approve_schedule) остаются без изменений
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

@router.post("/schedule/pin/{item_id}")
def pin_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(ScheduleItem).filter(ScheduleItem.id == item_id).first()
    if not item:
        return {"status": "error", "message": "Запись не найдена"}
    item.is_pinned = not item.is_pinned
    db.commit()
    return {"is_pinned": item.is_pinned}

@router.post("/schedule/approve")
def approve_schedule(db: Session = Depends(get_db)):
    from ..models import FinalScheduleItem
    db.query(FinalScheduleItem).delete()
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