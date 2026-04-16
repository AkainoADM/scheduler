# backend/app/generator.py
import random
from datetime import datetime
from collections import defaultdict
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from app.db import SessionLocal
from app.models import models
from app.config import settings

def parse_date(s: str):
    return datetime.strptime(s, settings.DATE_FORMAT).date()

def generate_schedule(group_ids: list[int], start_date_str: str, end_date_str: str, options: dict | None = None):
    start_date = parse_date(start_date_str)
    end_date = parse_date(end_date_str)
    db = SessionLocal()
    try:
        groups = db.query(models.RefGroup).filter(models.RefGroup.id.in_(group_ids)).all()
        time_slots = db.query(models.RefTimeSlot).filter(models.RefTimeSlot.is_active == True).order_by(models.RefTimeSlot.slot_number).all()
        working_dates = db.query(models.RefCalendar).filter(models.RefCalendar.date >= start_date, models.RefCalendar.date <= end_date, models.RefCalendar.is_working_day == True).order_by(models.RefCalendar.date).all()
        group_occ = defaultdict(set)
        teacher_occ = defaultdict(set)
        audience_occ = defaultdict(set)

        # helper functions
        def is_occupied(map_, date, slot_id, id_):
            return id_ in map_[(date, slot_id)]

        def mark_occupied(map_, date, slot_id, id_):
            map_[(date, slot_id)].add(id_)
        teacher_by_subject = defaultdict(list)
        rows = db.execute(text("SELECT teacher_id, subject_id FROM op_teachers_of_pairs")).all()
        for t_id, s_id in rows:
            teacher_by_subject[s_id].append(t_id)

        audience_by_subject = defaultdict(list)
        rows = db.execute(text("SELECT audience_id, subject_id FROM op_audiences_of_pairs")).all()
        for a_id, s_id in rows:
            audience_by_subject[s_id].append(a_id)

        # For each date -> group -> template lessons
        for cal in working_dates:
            date = cal.date
            for group in groups:
                # get templates for this group (adjust query to your schema)
                templates = db.query(models.OpTemplate).filter(models.OpTemplate.name_of_sample_id == group.id).all()
                for tpl in templates:
                    placed = False
                    for slot in time_slots:
                        slot_id = slot.id
                        # hard checks
                        if is_occupied(group_occ, date, slot_id, group.id):
                            continue

                        # pick teacher (first available)
                        teacher_id = None
                        for t in teacher_by_subject.get(tpl.lesson_id, []):
                            if not is_occupied(teacher_occ, date, slot_id, t):
                                teacher_id = t
                                break
                        if teacher_id is None:
                            # no teacher available for this slot
                            continue

                        # pick audience (prefer tpl.audience_id)
                        audience_id = tpl.audience_id if tpl.audience_id is not None else None
                        if audience_id is not None:
                            if is_occupied(audience_occ, date, slot_id, audience_id):
                                continue
                        else:
                            # choose any suitable audience
                            for a in audience_by_subject.get(tpl.lesson_id, []):
                                if not is_occupied(audience_occ, date, slot_id, a):
                                    audience_id = a
                                    break
                            if audience_id is None:
                                continue

                        # create lesson and schedule item
                        lesson = models.OpLesson(
                            text=f"Auto: subject {tpl.lesson_id}",
                            date=date,
                            subject_id=tpl.lesson_id,
                            insertion_id=None,
                            time_slot_id=slot_id,
                            week_day=cal.id
                        )
                        db.add(lesson)
                        db.flush()  # lesson.id available

                        schedule_item = models.OpScheduleItem(
                            lesson_id=lesson.id,
                            time_slot_id=slot_id,
                            audience_id=audience_id,
                            date=date,
                            status='OK'
                        )
                        db.add(schedule_item)

                        # mark occupied
                        mark_occupied(group_occ, date, slot_id, group.id)
                        mark_occupied(teacher_occ, date, slot_id, teacher_id)
                        mark_occupied(audience_occ, date, slot_id, audience_id)

                        placed = True
                        break

                    if not placed:
                        # лог конфликта — собираем в таблицу или лог
                        # Для MVP — просто печатаем
                        print(f"CONFLICT: group {group.id} tpl {tpl.id} date {date}")

        db.commit()
        return {"status": "ok", "message": "generation finished"}
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()
