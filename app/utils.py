import random
from datetime import date, timedelta
from collections import defaultdict
from sqlalchemy.orm import Session, joinedload, selectinload
from .models import ScheduleItem, ScheduleTemplate, Lesson, Subject, TimeSlot, Audience, TemplateItem
from datetime import date, timedelta
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

def get_date_range(start_date: date, end_date: date):
    from datetime import timedelta
    return [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]

def generate_schedule(db: Session, start_dt: datetime, end_dt: datetime):
    print(f"🚀 Запуск генерации: {start_dt} -> {end_dt}")
    
    # 1. Загружаем шаблоны (теперь они связаны напрямую с Subject)
    # Убедись, что в модели TemplateItem поле теперь называется subject_id
    all_templates = db.query(TemplateItem).all()

    if not all_templates:
        print("❌ ОШИБКА: Шаблоны не найдены в базе!")
        return 0

    created_count = 0
    current_date = start_dt

    while current_date <= end_dt:
        # ISO день недели: Пн=1, Вс=7
        day_of_week = current_date.weekday() + 1
        
        # Фильтруем шаблоны для текущего дня недели
        daily_items = [ti for ti in all_templates if ti.day_of_week_id == day_of_week]

        for ti in daily_items:
            try:
                # 2. СОЗДАЕМ НОВЫЙ УРОК (op_lessons)
                # Теперь берем subject_id напрямую из шаблона!
                new_lesson = Lesson(
                    subject_id=ti.subject_id, 
                    date=current_date,
                    student_count=0  # Или дефолтное значение
                )
                db.add(new_lesson)
                
                # Проталкиваем в базу, чтобы получить ID нового урока
                db.flush() 

                # 3. СОЗДАЕМ ЗАПИСЬ В РАСПИСАНИИ (op_schedule_items)
                new_item = ScheduleItem(
                    date=current_date,
                    lesson_id=new_lesson.id,  # Ссылка на свежесозданный урок
                    time_slot_id=ti.time_slot_id,
                    audience_id=ti.audience_id,
                    status="scheduled",
                    is_pinned=True
                )
                db.add(new_item)
                created_count += 1
                
            except Exception as e:
                print(f"⚠️ Ошибка при создании элемента для шаблона {ti.id}: {e}")
                db.rollback()
                continue

        current_date += timedelta(days=1)

    # Фиксируем все созданные уроки и расписание одним махом
    db.commit()
    print(f"✨ Успешно создано {created_count} занятий")
    return created_count
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
