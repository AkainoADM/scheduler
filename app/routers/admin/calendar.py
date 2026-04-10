from datetime import date
from typing import List
from fastapi import APIRouter, Depends, Form, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import calendar as calendar_service
from app.services import calendar_sync
from app.schemas.calendar import CalendarCreate, CalendarUpdate
from app.routers.admin.common import export_to_excel, _common_styles, _import_script
from app.services.audit import log_action

router = APIRouter(prefix="/admin/calendar", tags=["Admin Calendar"])

def render_calendar_html(entries):
    html = f"<h1>Календарь (учебные дни, праздники)</h1>{_common_styles()}"
    html += "<div><a href='/admin/calendar/export' class='btn-excel'>📎 Экспорт в Excel</a>"
    html += " <button onclick='toggleImportForm_calendar()' class='btn-excel btn-import'>📂 Импорт из Excel</button></div>"
    html += f"<div id='importForm_calendar' class='import-form'>"
    html += f"<form id='uploadForm_calendar' action='/admin/import/calendar' method='post' enctype='multipart/form-data'>"
    html += "<input type='file' name='file' accept='.xlsx,.xls' required>"
    html += "<button type='submit'>Загрузить</button>"
    html += "<button type='button' onclick='toggleImportForm_calendar()'>Отмена</button>"
    html += "</form></div>"
    html += _import_script("calendar")
    html += "<h2>Добавить запись</h2>"
    html += "<form method='post' action='/admin/calendar/add'>"
    html += "<input type='date' name='date' required>"
    html += "<select name='is_working_day'><option value='true'>Рабочий день</option><option value='false'>Выходной/праздник</option></select>"
    html += "<input type='text' name='description' placeholder='Описание'>"
    html += "<button type='submit'>Добавить</button>"
    html += "</form>"
    html += "<h2>Синхронизация с официальным календарем</h2>"
    html += "<form method='post' action='/admin/calendar/sync'>"
    html += "<input type='number' name='year' placeholder='Год (например, 2025)' required>"
    html += "<button type='submit'>Загрузить данные за год</button>"
    html += "</form>"
    html += "<h2>Список записей</h2>"
    html += "<form method='post' action='/admin/calendar/bulk-delete' onsubmit='return confirmDeleteSelected();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllCalendar'> Выделить всё</label>"
    html += "<ul>"
    for e in entries:
        html += f"<li><input type='checkbox' name='ids' value='{e.id}'> "
        html += f"{e.date} – {'Рабочий' if e.is_working_day else 'Выходной'} "
        if e.description:
            html += f"— {e.description} "
        html += f"<a href='/admin/calendar/edit/{e.id}'>Редактировать</a> "
        html += f"<a href='/admin/calendar/delete/{e.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<a href='/admin/'>На главную админки</a>"
    html += """
    <script>
        const selectAll = document.getElementById('selectAllCalendar');
        if (selectAll) {
            selectAll.addEventListener('change', function() {
                const checkboxes = document.querySelectorAll('input[name="ids"]');
                checkboxes.forEach(cb => cb.checked = selectAll.checked);
            });
        }
        function confirmDeleteSelected() {
            const anyChecked = document.querySelectorAll('input[name="ids"]:checked').length > 0;
            if (!anyChecked) { alert('Не выбрано ни одной записи'); return false; }
            return confirm('Вы уверены, что хотите удалить выбранные записи?');
        }
    </script>
    """
    return html

@router.get("", response_class=HTMLResponse)
async def calendar_page(db: AsyncSession = Depends(get_db)):
    entries = await calendar_service.get_all_calendar(db)
    return HTMLResponse(content=render_calendar_html(entries))

@router.post("/add", response_model=None)
async def add_calendar_entry(
    request: Request,
    date: date = Form(...),
    is_working_day: bool = Form(True),
    description: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = CalendarCreate(date=date, is_working_day=is_working_day, description=description)
    entry = await calendar_service.create_calendar_entry(db, data)
    await log_action(db, "create_calendar_entry", {"id": entry.id, "date": str(date), "is_working_day": is_working_day, "description": description}, request)
    return RedirectResponse(url="/admin/calendar", status_code=303)

@router.post("/sync", response_model=None)
async def sync_calendar_web(
    request: Request,
    year: int = Form(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db)
):
    background_tasks.add_task(calendar_sync.sync_calendar_for_year, year)
    await log_action(db, "sync_calendar", {"year": year}, request)
    return RedirectResponse(url="/admin/calendar", status_code=303)

@router.get("/edit/{entry_id}", response_class=HTMLResponse)
async def edit_calendar_form(entry_id: int, db: AsyncSession = Depends(get_db)):
    entry = await calendar_service.get_calendar_entry(db, entry_id)
    if not entry:
        return HTMLResponse("Запись не найдена", status_code=404)
    html = f"""
    <h1>Редактировать запись календаря</h1>
    <form method="post" action="/admin/calendar/edit/{entry_id}">
        <input type="date" name="date" value="{entry.date}" required>
        <select name="is_working_day">
            <option value="true" {'selected' if entry.is_working_day else ''}>Рабочий день</option>
            <option value="false" {'selected' if not entry.is_working_day else ''}>Выходной/праздник</option>
        </select>
        <input type="text" name="description" value="{entry.description or ''}">
        <button type="submit">Сохранить</button>
    </form>
    <a href="/admin/calendar">Отмена</a>
    """
    return HTMLResponse(content=html)

@router.post("/edit/{entry_id}", response_model=None)
async def edit_calendar_entry(
    request: Request,
    entry_id: int,
    date: date = Form(...),
    is_working_day: bool = Form(True),
    description: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = CalendarUpdate(date=date, is_working_day=is_working_day, description=description)
    await calendar_service.update_calendar_entry(db, entry_id, data)
    await log_action(db, "update_calendar_entry", {"id": entry_id, "date": str(date), "is_working_day": is_working_day, "description": description}, request)
    return RedirectResponse(url="/admin/calendar", status_code=303)

@router.get("/delete/{entry_id}", response_class=HTMLResponse)
async def confirm_delete_calendar(entry_id: int, db: AsyncSession = Depends(get_db)):
    entry = await calendar_service.get_calendar_entry(db, entry_id)
    if not entry:
        return HTMLResponse("Запись не найдена", status_code=404)
    html = f"""
    <h1>Удалить запись за {entry.date}?</h1>
    <form method="post" action="/admin/calendar/delete/{entry_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/calendar">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/delete/{entry_id}", response_model=None)
async def delete_calendar_entry(
    request: Request,
    entry_id: int,
    db: AsyncSession = Depends(get_db)
):
    await calendar_service.delete_calendar_entry(db, entry_id)
    await log_action(db, "delete_calendar_entry", {"id": entry_id}, request)
    return RedirectResponse(url="/admin/calendar", status_code=303)

@router.post("/bulk-delete", response_model=None)
async def bulk_delete_calendar(
    request: Request,
    ids: List[int] = Form(...),
    db: AsyncSession = Depends(get_db)
):
    await calendar_service.bulk_delete_calendar(db, ids)
    await log_action(db, "bulk_delete_calendar", {"ids": ids}, request)
    return RedirectResponse(url="/admin/calendar", status_code=303)

@router.get("/export")
async def export_calendar(db: AsyncSession = Depends(get_db)):
    entries = await calendar_service.get_all_calendar(db)
    data = [{"ID": e.id, "Дата": e.date, "Рабочий день": "Да" if e.is_working_day else "Нет", "Тип недели": e.week_type or "", "Описание": e.description or ""} for e in entries]
    return export_to_excel(data, ["ID", "Дата", "Рабочий день", "Тип недели", "Описание"], "Календарь", "calendar.xlsx")