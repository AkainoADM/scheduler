import random
from collections import defaultdict
from sqlalchemy.orm import Session, selectinload
from .models import ScheduleItem, Lesson, Audience, TimeSlot, Subject

def generate_schedule(db: Session):
    # Очищаем старое расписание
    db.query(ScheduleItem).delete()
    
    # Загружаем все уроки на все даты со связями
    lessons = db.query(Lesson).options(
        selectinload(Lesson.subject).selectinload(Subject.groups),
        selectinload(Lesson.subject).selectinload(Subject.teachers)
    ).all()
    
    active_audiences = db.query(Audience).filter(Audience.is_active == True).all()
    # Сортируем слоты по порядку (1 пара, 2 пара и т.д.)
    time_slots = db.query(TimeSlot).order_by(TimeSlot.slot_number).all()
    
    # Трекер занятости: timeline[дата][ID слота] = {'rooms': set(), 'teachers': set(), 'groups': set()}
    timeline = defaultdict(lambda: defaultdict(lambda: {'rooms': set(), 'teachers': set(), 'groups': set()}))
    
    new_schedule = []

    # Сортируем уроки так, чтобы сначала ставить сложные (потоковые лекции), а потом обычные
    lessons.sort(key=lambda x: (
        len(x.subject.groups) if x.subject else 0,
        len(x.subject.teachers) if x.subject else 0
    ), reverse=True)

    for lesson in lessons:
        subject = lesson.subject
        if not subject: continue
            
        group_ids = [g.id for g in subject.groups]
        teacher_ids = [t.id for t in subject.teachers]
        
        if not group_ids:
            continue # Пропускаем "пустые" предметы без групп

        l_date = lesson.date
        target_capacity = int(lesson.student_count or 0)
        placed = False

        # Ищем ПЕРВОЕ СВОБОДНОЕ время (чтобы не было пустых окон с утра)
        for slot in time_slots:
            state = timeline[l_date][slot.id]
            
            # ЖЕСТКИЕ ПРАВИЛА (Hard Rules)
            # 1. Занята ли хоть одна группа из этого предмета в это время?
            if any(g_id in state['groups'] for g_id in group_ids): continue
            # 2. Занят ли преподаватель в это время?
            if any(t_id in state['teachers'] for t_id in teacher_ids): continue
                
            # 3. Ищем подходящую свободную аудиторию
            available_rooms = [
                a for a in active_audiences 
                if a.id not in state['rooms'] and a.capacity >= target_capacity
            ]
            
            if not available_rooms: continue

            # Выбираем случайную подходящую аудиторию
            selected_room = random.choice(available_rooms)

            # БРОНИРУЕМ СЛОТ
            state['rooms'].add(selected_room.id)
            state['teachers'].update(teacher_ids)
            state['groups'].update(group_ids)

            # Создаем запись расписания
            new_item = ScheduleItem(
                lesson_id=lesson.id,
                time_slot_id=slot.id,
                audience_id=selected_room.id,
                date=l_date,
                status='scheduled'
            )
            new_schedule.append(new_item)
            placed = True
            break # Урок успешно поставлен, переходим к следующему
            
        if not placed:
            print(f"Не удалось найти слот для предмета {subject.name} на {l_date}")

    # Сохраняем в базу за один проход
    db.add_all(new_schedule)
    db.commit()
    return {"status": "success", "count": len(new_schedule)}