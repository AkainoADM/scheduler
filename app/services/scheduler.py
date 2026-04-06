import random
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, delete
from app.models.reference import ScheduleItem, Lesson, Audience, TimeSlot, Subject

async def generate_schedule(db: AsyncSession):
    # Удаляем только незакреплённые записи
    await db.execute(delete(ScheduleItem).where(ScheduleItem.is_pinned == False))
    await db.flush()

    # Загружаем закреплённые элементы, чтобы заблокировать их слоты
    pinned_result = await db.execute(select(ScheduleItem).where(ScheduleItem.is_pinned == True).options(
        selectinload(ScheduleItem.lesson).selectinload(Lesson.subject).selectinload(Subject.teachers),
        selectinload(ScheduleItem.lesson).selectinload(Lesson.subject).selectinload(Subject.groups)
    ))
    pinned_items = pinned_result.scalars().all()

    # timeline: dict[date, dict[slot_id, {'rooms': set(), 'teachers': set(), 'groups': set()}]]
    timeline = defaultdict(lambda: defaultdict(lambda: {'rooms': set(), 'teachers': set(), 'groups': set()}))

    for p in pinned_items:
        key = (p.date, p.time_slot_id)
        timeline[key]['rooms'].add(p.audience_id)
        if p.lesson and p.lesson.subject:
            timeline[key]['teachers'].update(t.id for t in p.lesson.subject.teachers)
            timeline[key]['groups'].update(g.id for g in p.lesson.subject.groups)

    # Загружаем уроки, которые ещё не в расписании (исключая закреплённые)
    pinned_lesson_ids = [p.lesson_id for p in pinned_items if p.lesson_id]
    stmt = select(Lesson).where(~Lesson.id.in_(pinned_lesson_ids) if pinned_lesson_ids else True).options(
        selectinload(Lesson.subject).selectinload(Subject.groups),
        selectinload(Lesson.subject).selectinload(Subject.teachers)
    )
    lessons_result = await db.execute(stmt)
    lessons = lessons_result.scalars().all()

    active_audiences_result = await db.execute(select(Audience).where(Audience.is_active == True))
    active_audiences = active_audiences_result.scalars().all()

    time_slots_result = await db.execute(select(TimeSlot).order_by(TimeSlot.slot_number))
    time_slots = time_slots_result.scalars().all()

    # Сортируем уроки: сложные (с большим количеством групп/преподавателей) первыми
    lessons.sort(key=lambda x: (
        len(x.subject.groups) if x.subject else 0,
        len(x.subject.teachers) if x.subject else 0
    ), reverse=True)

    new_schedule = []

    for lesson in lessons:
        subject = lesson.subject
        if not subject:
            continue
        group_ids = [g.id for g in subject.groups]
        teacher_ids = [t.id for t in subject.teachers]
        if not group_ids:
            continue
        l_date = lesson.date
        target_capacity = lesson.student_count or 0
        placed = False

        for slot in time_slots:
            state = timeline[l_date][slot.id]
            # Hard rules: группы и преподаватели не должны быть заняты
            if any(gid in state['groups'] for gid in group_ids):
                continue
            if any(tid in state['teachers'] for tid in teacher_ids):
                continue
            # Поиск свободной аудитории с достаточной вместимостью
            available_rooms = [
                a for a in active_audiences
                if a.id not in state['rooms'] and a.capacity >= target_capacity
            ]
            if not available_rooms:
                continue
            selected_room = random.choice(available_rooms)
            # Бронируем ресурсы
            state['rooms'].add(selected_room.id)
            state['teachers'].update(teacher_ids)
            state['groups'].update(group_ids)

            new_item = ScheduleItem(
                lesson_id=lesson.id,
                time_slot_id=slot.id,
                audience_id=selected_room.id,
                date=l_date,
                status='scheduled',
                is_pinned=False
            )
            new_schedule.append(new_item)
            placed = True
            break
        if not placed:
            print(f"Не удалось найти слот для предмета {subject.name} на {l_date}")

    db.add_all(new_schedule)
    await db.commit()
    return {"status": "success", "count": len(new_schedule)}