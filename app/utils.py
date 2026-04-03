import random
from datetime import date, timedelta
from collections import defaultdict
from sqlalchemy.orm import Session, selectinload
from .models import ScheduleItem, Lesson, Audience, TemplateItem, TimeSlot, Subject, FinalScheduleItem
from datetime import date, timedelta

def get_date_range(start_date: date, end_date: date):
    from datetime import timedelta
    return [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]

def generate_schedule(db: Session, start_date: date, end_date: date):
    # 1. Генерируем список дат
    dates = get_date_range(start_date, end_date)
    
    # 2. Очищаем только НЕЗАКРЕПЛЕННЫЕ записи за выбранный период
    db.query(ScheduleItem).filter(
        ScheduleItem.date >= start_date,
        ScheduleItem.date <= end_date,
        ScheduleItem.is_pinned == False
    ).delete()
    db.commit()

    # 3. Загружаем ВСЕ закрепленные (шаблонные) записи, чтобы знать, что занято
    pinned_items = db.query(ScheduleItem).filter(
        ScheduleItem.date >= start_date,
        ScheduleItem.date <= end_date,
        ScheduleItem.is_pinned == True
    ).options(selectinload(ScheduleItem.lesson)).all()

    # Трекер занятости: timeline[дата][ID слота]
    timeline = defaultdict(lambda: defaultdict(lambda: {'rooms': set(), 'teachers': set(), 'groups': set()}))

    # Заполняем трекер данными из шаблонов
    pinned_lesson_ids = set()
    for p in pinned_items:
        pinned_lesson_ids.add(p.lesson_id)
        state = timeline[p.date][p.time_slot_id]
        state['rooms'].add(p.audience_id)
        
        if p.lesson:
            # Предполагаем, что связи называются teachers и groups
            state['teachers'].update([t.id for t in p.lesson.teachers])
            state['groups'].update([g.id for g in p.lesson.groups])

    # 4. Загружаем уроки, которых нет в шаблонах (которые нужно распределить)
    lessons_to_place = db.query(Lesson).filter(
        ~Lesson.id.in_(pinned_lesson_ids)
    ).options(
        selectinload(Lesson.subject).selectinload(Subject.groups),
        selectinload(Lesson.subject).selectinload(Subject.teachers)
    ).all()

    active_audiences = db.query(Audience).filter(Audience.is_active == True).all()
    time_slots = db.query(TimeSlot).order_by(TimeSlot.slot_number).all()
    
    new_schedule = []

    # Сортируем уроки (сначала те, где больше групп — лекции)
    lessons_to_place.sort(key=lambda x: len(x.subject.groups) if x.subject else 0, reverse=True)

    # 5. ГЛАВНЫЙ ЦИКЛ ПО ДАТАМ И УРОКАМ
    for current_date in dates:
        for lesson in lessons_to_place:
            subject = lesson.subject
            if not subject: continue
            
            group_ids = [g.id for g in subject.groups]
            teacher_ids = [t.id for t in subject.teachers]
            target_capacity = int(lesson.student_count or 0)
            
            placed = False
            for slot in time_slots:
                state = timeline[current_date][slot.id]
                
                # Проверка конфликтов
                if any(g_id in state['groups'] for g_id in group_ids): continue
                if any(t_id in state['teachers'] for t_id in teacher_ids): continue
                
                # Поиск аудитории
                available_rooms = [
                    a for a in active_audiences 
                    if a.id not in state['rooms'] and a.capacity >= target_capacity
                ]
                
                if not available_rooms: continue

                selected_room = random.choice(available_rooms)

                # Бронируем
                state['rooms'].add(selected_room.id)
                state['teachers'].update(teacher_ids)
                state['groups'].update(group_ids)

                # Добавляем в список на сохранение
                new_item = ScheduleItem(
                    lesson_id=lesson.id,
                    time_slot_id=slot.id,
                    audience_id=selected_room.id,
                    date=current_date,
                    is_pinned=False,
                    status='scheduled'
                )
                new_schedule.append(new_item)
                placed = True
                break 
            
            if not placed:
                print(f"Предупреждение: Не удалось поставить {subject.name} на {current_date}")

    # 6. Сохранение
    db.add_all(new_schedule)
    db.commit()
    return {"status": "success", "added": len(new_schedule)}
def apply_template_to_period(db: Session, sample_id: int, start_date: date, end_date: date):
    # 1. Получаем правила из шаблона
    template_rules = db.query(TemplateItem).filter(TemplateItem.name_of_sample_id == sample_id).all()
    
    # 2. ОПРЕДЕЛЯЕМ date_range
    date_range = get_date_range(start_date, end_date)
    
    generated_items = []

    # 3. Теперь цикл по date_range будет работать
    for current_date in date_range:
        # В БД: 1=Пн, 2=Вт ... 7=Вс
        # В Python: .weekday() возвращает 0=Пн, 1=Вт ... 6=Вс
        db_weekday_id = current_date.weekday() + 1 
        
        daily_rules = [r for r in template_rules if r.day_of_week_id == db_weekday_id]
        
        for rule in daily_rules:
            new_item = ScheduleItem(
                lesson_id=rule.lesson_id,
                time_slot_id=rule.time_slot_id,
                audience_id=rule.audience_id,
                date=current_date,
                is_pinned=True,
                status='scheduled'
            )
            generated_items.append(new_item)
            
    if generated_items:
        db.add_all(generated_items)
        db.commit()
    
    return len(generated_items)
