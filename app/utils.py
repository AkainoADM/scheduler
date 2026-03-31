import random
from sqlalchemy.orm import Session, joinedload, selectinload
from .models import ScheduleItem, Lesson, Audience, TimeSlot

def generate_schedule(db: Session):
    # 1. Очистка старого расписания
    db.query(ScheduleItem).delete()
    
    # 2. Загрузка данных. ОБЯЗАТЕЛЬНО подгружаем группы и учителей
    lessons = db.query(Lesson).options(
        selectinload(Lesson.groups),
        selectinload(Lesson.teachers)
    ).all()
    
    # ПЕРЕМЕШИВАЕМ уроки для эффекта рандома
    random.shuffle(lessons)
    
    active_audiences = db.query(Audience).filter(Audience.is_active == True).all()
    time_slots = db.query(TimeSlot).all()
    
    timeline = {}
    new_schedule = []

    for lesson in lessons:
        # Проверяем, есть ли вообще у урока группы и учителя
        # Если их нет в БД, в таблице будут прочерки!
        teacher_ids = [t.id for t in lesson.teachers]
        group_ids = [g.id for g in lesson.groups]
        
        # Если урок "пустой", пропустим его или выведем в лог
        if not group_ids:
            print(f"Warning: У урока {lesson.subject} (ID: {lesson.id}) нет групп!")

        l_date = lesson.date
        target_capacity = int(lesson.student_count or 0)
        
        # Перемешиваем слоты, чтобы пары не всегда шли с первой
        shuffled_slots = list(time_slots)
        random.shuffle(shuffled_slots)

        for slot in shuffled_slots:
            key = (l_date, slot.id)
            if key not in timeline:
                timeline[key] = {'rooms': set(), 'groups': set(), 'teachers': set()}
            
            # Проверки на занятость (Hard Rules)
            if any(t_id in timeline[key]['teachers'] for t_id in teacher_ids): continue
            if any(g_id in timeline[key]['groups'] for g_id in group_ids): continue
                
            available_rooms = [
                a for a in active_audiences 
                if a.id not in timeline[key]['rooms'] and a.capacity >= target_capacity
            ]
            
            if not available_rooms: continue

            # Выбираем случайную подходящую комнату
            selected_room = random.choice(available_rooms)

            # Бронируем
            timeline[key]['rooms'].add(selected_room.id)
            timeline[key]['teachers'].update(teacher_ids)
            timeline[key]['groups'].update(group_ids)

            new_item = ScheduleItem(
                lesson_id=lesson.id,
                time_slot_id=slot.id,
                audience_id=selected_room.id,
                date=l_date,
                status='scheduled'
            )
            new_schedule.append(new_item)
            break
            
    db.add_all(new_schedule)
    db.commit()
    return {"status": "success", "count": len(new_schedule)}