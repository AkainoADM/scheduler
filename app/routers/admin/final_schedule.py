from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.reference import FinalScheduleItem, Lesson
from app.routers.admin.common import export_to_excel, _common_styles

router = APIRouter(prefix="/admin/final-schedule", tags=["Admin Final Schedule"])

@router.get("", response_class=HTMLResponse)
async def final_schedule_page(db: AsyncSession = Depends(get_db)):
    items = await db.execute(
        select(FinalScheduleItem)
        .options(
            selectinload(FinalScheduleItem.lesson).selectinload(Lesson.subject),
            selectinload(FinalScheduleItem.time_slot),
            selectinload(FinalScheduleItem.audience)
        )
        .order_by(FinalScheduleItem.date, FinalScheduleItem.time_slot_id)
    )
    items = items.scalars().all()
    rows = []
    for item in items:
        lesson = item.lesson
        subject = lesson.subject if lesson else None
        rows.append({
            "date": item.date,
            "subject": subject.name if subject else "—",
            "time_slot": item.time_slot.name if item.time_slot else "—",
            "audience": item.audience.name if item.audience else "—",
        })
    html = f"""
    <html>
    <head><title>Опубликованное расписание</title>{_common_styles()}</head>
    <body>
        <h1>Опубликованное расписание</h1>
        <div><a href="/admin/final-schedule/export" class="btn-excel">📎 Экспорт в Excel</a></div>
        <table border="1" style="width:100%; margin-top:20px;">
            <thead><tr><th>Дата</th><th>Предмет</th><th>Время</th><th>Аудитория</th></tr></thead>
            <tbody>
    """
    for row in rows:
        html += f"<tr><td>{row['date']}</td><td>{row['subject']}</td><td>{row['time_slot']}</td><td>{row['audience']}</td></tr>"
    html += """
            </tbody>
        </table>
        <br><a href="/admin/">На главную админки</a>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@router.get("/export")
async def export_final_schedule(db: AsyncSession = Depends(get_db)):
    items = await db.execute(
        select(FinalScheduleItem)
        .options(
            selectinload(FinalScheduleItem.lesson).selectinload(Lesson.subject),
            selectinload(FinalScheduleItem.time_slot),
            selectinload(FinalScheduleItem.audience)
        )
    )
    items = items.scalars().all()
    data = []
    for item in items:
        lesson = item.lesson
        subject = lesson.subject if lesson else None
        data.append({
            "Дата": item.date,
            "Предмет": subject.name if subject else "—",
            "Время": item.time_slot.name if item.time_slot else "—",
            "Аудитория": item.audience.name if item.audience else "—",
        })
    columns = ["Дата", "Предмет", "Время", "Аудитория"]
    return export_to_excel(data, columns, "Опубликованное расписание", "final_schedule.xlsx")