from datetime import date
from typing import List
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.services import audience as audience_service
from app.services import time_slot as time_slot_service
from app.models.reference import ScheduleItem, FinalScheduleItem, Lesson
from app.routers.admin.common import export_to_excel, _common_styles
from app.services.audit import log_action

router = APIRouter(prefix="/admin/schedule-editor", tags=["Admin Schedule Editor"])

@router.get("", response_class=HTMLResponse)
async def schedule_editor_page(db: AsyncSession = Depends(get_db)):
    items = await db.execute(
        select(ScheduleItem)
        .options(
            selectinload(ScheduleItem.lesson).selectinload(Lesson.subject),
            selectinload(ScheduleItem.time_slot),
            selectinload(ScheduleItem.audience)
        )
        .order_by(ScheduleItem.date, ScheduleItem.time_slot_id)
    )
    items = items.scalars().all()
    audiences = await audience_service.get_all_audiences(db)
    time_slots = await time_slot_service.get_all_time_slots(db)

    rows = []
    for item in items:
        lesson = item.lesson
        subject = lesson.subject if lesson else None
        rows.append({
            "id": item.id,
            "date": item.date,
            "subject": subject.name if subject else "—",
            "time_slot": item.time_slot,
            "audience": item.audience,
            "lesson_id": lesson.id if lesson else None,
        })

    html = f"""
    <html>
    <head>
        <title>Редактор черновика расписания</title>
        {_common_styles()}
        <style>
            .edit-form {{ display: inline; margin-left: 10px; }}
            select, input {{ padding: 4px; margin: 2px; }}
            button {{ margin: 2px; }}
        </style>
    </head>
    <body>
        <h1>Черновик расписания</h1>
        <div><a href="/admin/schedule-editor/export" class="btn-excel">📎 Экспорт черновика в Excel</a></div>
        <div style="margin-top: 20px;">
            <form method="post" action="/admin/schedule-editor/approve" onsubmit="return confirm('Утвердить расписание? Текущее опубликованное будет заменено.');">
                <button type="submit" class="btn" style="background: #28a745;">✅ Утвердить расписание</button>
            </form>
        </div>
        <table border="1" style="width:100%; margin-top:20px;">
            <thead>
                <tr><th>ID</th><th>Дата</th><th>Предмет</th><th>Время</th><th>Аудитория</th><th>Действия</th></tr>
            </thead>
            <tbody>
    """
    for row in rows:
        audience_options = ""
        for a in audiences:
            selected = "selected" if row["audience"] and a.id == row["audience"].id else ""
            audience_options += f'<option value="{a.id}" {selected}>{a.name}</option>'
        time_slot_options = ""
        for ts in time_slots:
            selected = "selected" if row["time_slot"] and ts.id == row["time_slot"].id else ""
            time_slot_options += f'<option value="{ts.id}" {selected}>{ts.name} ({ts.start_time}-{ts.end_time})</option>'

        html += f"""
            <tr>
                <td>{row["id"]}</td>
                <td><input type="date" name="date_{row["id"]}" value="{row["date"]}" form="edit_{row["id"]}" style="width:120px;"></td>
                <td>{row["subject"]}</td>
                <td><select name="time_slot_id_{row["id"]}" form="edit_{row["id"]}">{time_slot_options}</select></td>
                <td><select name="audience_id_{row["id"]}" form="edit_{row["id"]}">{audience_options}</select></td>
                <td>
                    <form id="edit_{row["id"]}" method="post" action="/admin/schedule-editor/update/{row["id"]}" style="display:inline;">
                        <button type="submit">Сохранить</button>
                    </form>
                    <a href="/admin/schedule-editor/delete/{row["id"]}" onclick="return confirm('Удалить занятие из черновика?');">Удалить</a>
                </td>
            </tr>
        """
    html += """
            </tbody>
        </table>
        <br><a href="/admin/">На главную админки</a>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@router.post("/update/{item_id}", response_model=None)
async def update_schedule_item(
    request: Request,
    item_id: int,
    date: date = Form(...),
    time_slot_id: int = Form(...),
    audience_id: int = Form(...),
    db: AsyncSession = Depends(get_db)
):
    item = await db.get(ScheduleItem, item_id)
    if item:
        item.date = date
        item.time_slot_id = time_slot_id
        item.audience_id = audience_id
        await db.commit()
        await log_action(db, "update_schedule_item", {"id": item_id, "date": str(date), "time_slot_id": time_slot_id, "audience_id": audience_id}, request)
    return RedirectResponse(url="/admin/schedule-editor", status_code=303)

@router.get("/delete/{item_id}", response_class=HTMLResponse)
async def confirm_delete_schedule_item(item_id: int, db: AsyncSession = Depends(get_db)):
    item = await db.get(ScheduleItem, item_id)
    if not item:
        return HTMLResponse("Запись не найдена", status_code=404)
    html = f"""
    <h1>Удалить занятие из черновика?</h1>
    <p>ID: {item.id}, Дата: {item.date}</p>
    <form method="post" action="/admin/schedule-editor/delete/{item_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/schedule-editor">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/delete/{item_id}", response_model=None)
async def delete_schedule_item(
    request: Request,
    item_id: int,
    db: AsyncSession = Depends(get_db)
):
    await db.execute(delete(ScheduleItem).where(ScheduleItem.id == item_id))
    await db.commit()
    await log_action(db, "delete_schedule_item", {"id": item_id}, request)
    return RedirectResponse(url="/admin/schedule-editor", status_code=303)

@router.post("/approve", response_model=None)
async def approve_schedule(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    await db.execute(delete(FinalScheduleItem))
    drafts = await db.execute(select(ScheduleItem))
    drafts = drafts.scalars().all()
    for d in drafts:
        final = FinalScheduleItem(
            lesson_id=d.lesson_id,
            time_slot_id=d.time_slot_id,
            audience_id=d.audience_id,
            date=d.date
        )
        db.add(final)
    await db.commit()
    await log_action(db, "approve_schedule", {"count": len(drafts)}, request)
    return RedirectResponse(url="/admin/schedule-editor", status_code=303)

@router.get("/export")
async def export_schedule_items(db: AsyncSession = Depends(get_db)):
    items = await db.execute(
        select(ScheduleItem)
        .options(
            selectinload(ScheduleItem.lesson).selectinload(Lesson.subject),
            selectinload(ScheduleItem.time_slot),
            selectinload(ScheduleItem.audience)
        )
    )
    items = items.scalars().all()
    data = []
    for item in items:
        lesson = item.lesson
        subject = lesson.subject if lesson else None
        data.append({
            "ID": item.id,
            "Дата": item.date,
            "Предмет": subject.name if subject else "—",
            "Время": item.time_slot.name if item.time_slot else "—",
            "Аудитория": item.audience.name if item.audience else "—",
            "Закреплено": "Да" if item.is_pinned else "Нет"
        })
    columns = ["ID", "Дата", "Предмет", "Время", "Аудитория", "Закреплено"]
    return export_to_excel(data, columns, "Черновик расписания", "schedule_items.xlsx")