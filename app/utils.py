import random
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .models import Timetable, Discipline, Group, Audience
from fastapi.responses import HTMLResponse
from .database import get_db

def generate_schedule(db: Session):
    db.query(Timetable).delete()
    
    lessons = db.query(Discipline).all()
    groups = db.query(Group).all()
    audiences = db.query(Audience).all()

    if not lessons or not groups or not audiences:
        raise HTTPException(status_code=400, detail="Справочники пусты. Добавьте группы, аудитории и предметы.")
    
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница"]
    pairs = [1, 2, 3, 4] 
    new_entries = []
    workload = list(lessons) * 2 

    for day in days:
        group_daily_load = {g.id: 0 for g in groups}
        max_pairs_per_day = 3 # Настрой этот параметр

        for pair in pairs:
            busy_teachers = set()
            busy_rooms = set()
            
            shuffled_groups = list(groups)
            random.shuffle(shuffled_groups)

            for group in shuffled_groups:
                # Проверка: не превышен ли лимит пар для группы сегодня
                if group_daily_load[group.id] >= max_pairs_per_day:
                    continue

                # Фильтруем предметы: преподаватель свободен + этот предмет еще остался в плане
                available_lessons = [
                    l for l in workload 
                    if l.teacher_id not in busy_teachers
                ]
                
                available_rooms = [
                    r for r in audiences 
                    if r.id not in busy_rooms and (int(r.capacity or 0) >= int(group.student_count or 0))  # type: ignore
                ]
                
                if not available_lessons or not available_rooms:
                    continue

                selected_lesson = random.choice(available_lessons)
                selected_room = random.choice(available_rooms)

                # Занимаем ресурсы
                busy_teachers.add(selected_lesson.teacher_id)
                busy_rooms.add(selected_room.id)
                group_daily_load[group.id] += 1
                
                # Убираем этот "час" из нагрузки, чтобы не превысить план
                workload.remove(selected_lesson)

                new_entries.append(Timetable(
                    discipline_id=selected_lesson.id,
                    group_id=group.id,
                    audience_id=selected_room.id,
                    day_of_week=day,
                    lesson_number=pair
                ))

    db.add_all(new_entries)
    db.commit()
    return {"status": "success", "count": len(new_entries)}