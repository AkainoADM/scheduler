from typing import List
from datetime import time
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import time_slot as time_slot_service
from app.schemas.time_slot import TimeSlotCreate, TimeSlotUpdate
from app.routers.admin.common import export_to_excel, _common_styles, _import_script
from app.services.audit import log_action

router = APIRouter(prefix="/admin/time-slots", tags=["Admin Time Slots"])

def render_time_slots_html(time_slots):
    html = f"<h1>Временные слоты (пары)</h1>{_common_styles()}"
    html += "<div><a href='/admin/time-slots/export' class='btn-excel'>📎 Экспорт в Excel</a>"
    html += " <button onclick='toggleImportForm_time_slots()' class='btn-excel btn-import'>📂 Импорт из Excel</button></div>"
    html += f"<div id='importForm_time_slots' class='import-form'>"
    html += f"<form id='uploadForm_time_slots' action='/admin/import/time_slots' method='post' enctype='multipart/form-data'>"
    html += "<input type='file' name='file' accept='.xlsx,.xls' required>"
    html += "<button type='submit'>Загрузить</button>"
    html += "<button type='button' onclick='toggleImportForm_time_slots()'>Отмена</button>"
    html += "</form></div>"
    html += _import_script("time_slots")
    html += "<form method='post' action='/admin/time-slots/add'>"
    html += "<input type='number' name='slot_number' placeholder='Номер пары' required>"
    html += "<input type='text' name='name' placeholder='Название (например, 1 пара)' required>"
    html += "<input type='time' name='start_time' placeholder='Время начала (HH:MM)' required>"
    html += "<input type='time' name='end_time' placeholder='Время окончания (HH:MM)' required>"
    html += "<input type='number' name='duration_minutes' placeholder='Длительность (мин)'>"
    html += "<input type='number' name='break_after_minutes' placeholder='Перерыв после (мин)'>"
    html += "<label><input type='checkbox' name='is_active' value='true' checked> Активен</label>"
    html += "<button type='submit'>Добавить</button>"
    html += "</form>"
    html += "<form method='post' action='/admin/time-slots/bulk-delete' onsubmit='return confirmDeleteSelected();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllTimeSlots'> Выделить всё</label>"
    html += "<ul>"
    for ts in time_slots:
        html += f"<li><input type='checkbox' name='ids' value='{ts.id}'> "
        html += f"{ts.name} (№{ts.slot_number}, {ts.start_time}–{ts.end_time})"
        if ts.duration_minutes:
            html += f", длительность: {ts.duration_minutes} мин"
        if not ts.is_active:
            html += " [неактивен]"
        html += f" <a href='/admin/time-slots/edit/{ts.id}'>Редактировать</a> "
        html += f"<a href='/admin/time-slots/delete/{ts.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<a href='/admin/'>На главную админки</a>"
    html += """
    <script>
        const selectAll = document.getElementById('selectAllTimeSlots');
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
async def time_slots_page(db: AsyncSession = Depends(get_db)):
    time_slots = await time_slot_service.get_all_time_slots(db)
    return HTMLResponse(content=render_time_slots_html(time_slots))

@router.post("/add", response_model=None)
async def add_time_slot(
    request: Request,
    slot_number: int = Form(...),
    name: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    duration_minutes: int = Form(None),
    break_after_minutes: int = Form(None),
    is_active: bool = Form(True),
    db: AsyncSession = Depends(get_db)
):
    start = time.fromisoformat(start_time)
    end = time.fromisoformat(end_time)
    data = TimeSlotCreate(slot_number=slot_number, name=name, start_time=start, end_time=end, duration_minutes=duration_minutes, break_after_minutes=break_after_minutes, is_active=is_active)
    ts = await time_slot_service.create_time_slot(db, data)
    await log_action(db, "create_time_slot", {"id": ts.id, "slot_number": slot_number, "name": name, "start_time": start_time, "end_time": end_time, "duration_minutes": duration_minutes, "break_after_minutes": break_after_minutes, "is_active": is_active}, request)
    return RedirectResponse(url="/admin/time-slots", status_code=303)

@router.get("/edit/{ts_id}", response_class=HTMLResponse)
async def edit_time_slot_form(ts_id: int, db: AsyncSession = Depends(get_db)):
    ts = await time_slot_service.get_time_slot(db, ts_id)
    if not ts:
        return HTMLResponse("Слот не найден", status_code=404)
    html = f"""
    <h1>Редактировать временной слот</h1>
    <form method="post" action="/admin/time-slots/edit/{ts_id}">
        <input type="number" name="slot_number" value="{ts.slot_number}" required>
        <input type="text" name="name" value="{ts.name}" required>
        <input type="time" name="start_time" value="{ts.start_time.isoformat()}" required>
        <input type="time" name="end_time" value="{ts.end_time.isoformat()}" required>
        <input type="number" name="duration_minutes" value="{ts.duration_minutes or ''}">
        <input type="number" name="break_after_minutes" value="{ts.break_after_minutes or ''}">
        <label><input type="checkbox" name="is_active" value="true" {'checked' if ts.is_active else ''}> Активен</label>
        <button type="submit">Сохранить</button>
    </form>
    <a href="/admin/time-slots">Отмена</a>
    """
    return HTMLResponse(content=html)

@router.post("/edit/{ts_id}", response_model=None)
async def edit_time_slot(
    request: Request,
    ts_id: int,
    slot_number: int = Form(...),
    name: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    duration_minutes: int = Form(None),
    break_after_minutes: int = Form(None),
    is_active: bool = Form(True),
    db: AsyncSession = Depends(get_db)
):
    start = time.fromisoformat(start_time)
    end = time.fromisoformat(end_time)
    data = TimeSlotUpdate(slot_number=slot_number, name=name, start_time=start, end_time=end, duration_minutes=duration_minutes, break_after_minutes=break_after_minutes, is_active=is_active)
    await time_slot_service.update_time_slot(db, ts_id, data)
    await log_action(db, "update_time_slot", {"id": ts_id, "slot_number": slot_number, "name": name, "start_time": start_time, "end_time": end_time, "duration_minutes": duration_minutes, "break_after_minutes": break_after_minutes, "is_active": is_active}, request)
    return RedirectResponse(url="/admin/time-slots", status_code=303)

@router.get("/delete/{ts_id}", response_class=HTMLResponse)
async def confirm_delete_time_slot(ts_id: int, db: AsyncSession = Depends(get_db)):
    ts = await time_slot_service.get_time_slot(db, ts_id)
    if not ts:
        return HTMLResponse("Слот не найден", status_code=404)
    html = f"""
    <h1>Удалить слот "{ts.name}"?</h1>
    <form method="post" action="/admin/time-slots/delete/{ts_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/time-slots">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/delete/{ts_id}", response_model=None)
async def delete_time_slot(
    request: Request,
    ts_id: int,
    db: AsyncSession = Depends(get_db)
):
    await time_slot_service.delete_time_slot(db, ts_id)
    await log_action(db, "delete_time_slot", {"id": ts_id}, request)
    return RedirectResponse(url="/admin/time-slots", status_code=303)

@router.post("/bulk-delete", response_model=None)
async def bulk_delete_time_slots(
    request: Request,
    ids: List[int] = Form(...),
    db: AsyncSession = Depends(get_db)
):
    await time_slot_service.bulk_delete_time_slots(db, ids)
    await log_action(db, "bulk_delete_time_slots", {"ids": ids}, request)
    return RedirectResponse(url="/admin/time-slots", status_code=303)

@router.get("/export")
async def export_time_slots(db: AsyncSession = Depends(get_db)):
    slots = await time_slot_service.get_all_time_slots(db)
    data = [{"ID": s.id, "Номер": s.slot_number, "Название": s.name, "Начало": str(s.start_time), "Конец": str(s.end_time), "Длительность(мин)": s.duration_minutes or "", "Перерыв(мин)": s.break_after_minutes or "", "Активен": "Да" if s.is_active else "Нет"} for s in slots]
    return export_to_excel(data, ["ID", "Номер", "Название", "Начало", "Конец", "Длительность(мин)", "Перерыв(мин)", "Активен"], "Временные слоты", "time_slots.xlsx")