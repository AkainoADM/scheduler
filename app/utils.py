import random
from sqlalchemy.orm import Session
from .models import ScheduleItem, Lesson, Audience, TimeSlot
def generate_schedule(db: Session):
    db.query(ScheduleItem).delete()
    lessons = db.query(Lesson).all()
    audiences = db.query(Audience).filter(Audience.is_active == True).all()
    time_slots = db.query(TimeSlot).order_by(TimeSlot.slot_number).all()

    if not lessons or not audiences or not time_slots:
        return 0 

    new_schedule = []
    for lesson in lessons:
        suitable_audiences = [a for a in audiences if a.capacity is not None and a.capacity >= lesson.student_count]  # type: ignore
        if not suitable_audiences:
            suitable_audiences = audiences
            
        selected_audience = random.choice(suitable_audiences)
        selected_slot = random.choice(time_slots)

        new_schedule.append(ScheduleItem(
            lesson_id=lesson.id,
            time_slot_id=selected_slot.id,
            audience_id=selected_audience.id,
            date=lesson.date,
            status='scheduled'
        ))

    db.add_all(new_schedule)
    db.commit()
    return len(new_schedule)