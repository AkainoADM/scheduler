from typing import List
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import audience as audience_service
from app.services import building as building_service
from app.schemas.audience import AudienceCreate, AudienceUpdate
from app.routers.admin.common import export_to_excel, _common_styles, _import_script, has_dependent_audience_subjects
from app.services.audit import log_action

router = APIRouter(prefix="/admin/audiences", tags=["Admin Audiences"])

def render_audiences_html(audiences, buildings):
    html = f"<h1>Аудитории</h1>{_common_styles()}"
    html += "<div><a href='/admin/audiences/export' class='btn-excel'>📎 Экспорт в Excel</a>"
    html += " <button onclick='toggleImportForm_audiences()' class='btn-excel btn-import'>📂 Импорт из Excel</button></div>"
    html += f"<div id='importForm_audiences' class='import-form'>"
    html += f"<form id='uploadForm_audiences' action='/admin/import/audiences' method='post' enctype='multipart/form-data'>"
    html += "<input type='file' name='file' accept='.xlsx,.xls' required>"
    html += "<button type='submit'>Загрузить</button>"
    html += "<button type='button' onclick='toggleImportForm_audiences()'>Отмена</button>"
    html += "</form></div>"
    html += _import_script("audiences")
    html += "<form method='post' action='/admin/audiences/add'>"
    html += "<input type='text' name='name' placeholder='Номер/название' required>"
    html += "<select name='building_id'><option value=''>Не выбрано</option>"
    for b in buildings:
        html += f"<option value='{b.id}'>{b.name}</option>"
    html += "</select>"
    html += "<input type='number' name='capacity' placeholder='Вместимость'>"
    html += "<select name='type'><option value=''>Тип</option><option value='лекционная'>Лекционная</option><option value='практическая'>Практическая</option><option value='лабораторная'>Лабораторная</option><option value='компьютерный класс'>Компьютерный класс</option></select>"
    html += "<label><input type='checkbox' name='is_active' value='true' checked> Активна</label>"
    html += "<button type='submit'>Добавить</button>"
    html += "</form>"
    html += "<form method='post' action='/admin/audiences/bulk-delete' onsubmit='return confirmDeleteSelected();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllAudiences'> Выделить всё</label>"
    html += "<ul>"
    for a in audiences:
        html += f"<li><input type='checkbox' name='ids' value='{a.id}'> "
        html += f"{a.name} (Корпус ID: {a.building_id or 'не указан'}, Мест: {a.capacity or 'не указано'}, Тип: {a.type or 'не указан'}, Активна: {a.is_active}) "
        html += f"<a href='/admin/audiences/edit/{a.id}'>Редактировать</a> "
        html += f"<a href='/admin/audiences/delete/{a.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<a href='/admin/'>На главную админки</a>"
    html += """
    <script>
        const selectAll = document.getElementById('selectAllAudiences');
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
async def audiences_page(db: AsyncSession = Depends(get_db)):
    audiences = await audience_service.get_all_audiences(db)
    buildings = await building_service.get_all_buildings(db)
    return HTMLResponse(content=render_audiences_html(audiences, buildings))

@router.post("/add", response_model=None)
async def add_audience(
    request: Request,
    name: str = Form(...),
    building_id: int = Form(None),
    capacity: int = Form(None),
    type: str = Form(None),
    is_active: bool = Form(True),
    db: AsyncSession = Depends(get_db)
):
    data = AudienceCreate(name=name, building_id=building_id, capacity=capacity, type=type, is_active=is_active)
    audience = await audience_service.create_audience(db, data)
    await log_action(db, "create_audience", {"id": audience.id, "name": name, "building_id": building_id, "capacity": capacity, "type": type, "is_active": is_active}, request)
    return RedirectResponse(url="/admin/audiences", status_code=303)

@router.get("/edit/{audience_id}", response_class=HTMLResponse)
async def edit_audience_form(audience_id: int, db: AsyncSession = Depends(get_db)):
    audience = await audience_service.get_audience(db, audience_id)
    if not audience:
        return HTMLResponse("Аудитория не найдена", status_code=404)
    buildings = await building_service.get_all_buildings(db)
    html = f"""
    <h1>Редактировать аудиторию</h1>
    <form method="post" action="/admin/audiences/edit/{audience_id}">
        <input type="text" name="name" value="{audience.name}" required>
        <select name="building_id">
            <option value="">Не выбрано</option>
            {''.join(f'<option value="{b.id}" {"selected" if b.id == audience.building_id else ""}>{b.name}</option>' for b in buildings)}
        </select>
        <input type="number" name="capacity" value="{audience.capacity or ''}">
        <select name="type">
            <option value="">Тип</option>
            <option value="лекционная" {'selected' if audience.type == 'лекционная' else ''}>Лекционная</option>
            <option value="практическая" {'selected' if audience.type == 'практическая' else ''}>Практическая</option>
            <option value="лабораторная" {'selected' if audience.type == 'лабораторная' else ''}>Лабораторная</option>
            <option value="компьютерный класс" {'selected' if audience.type == 'компьютерный класс' else ''}>Компьютерный класс</option>
        </select>
        <label><input type="checkbox" name="is_active" value="true" {'checked' if audience.is_active else ''}> Активна</label>
        <button type="submit">Сохранить</button>
    </form>
    <a href="/admin/audiences">Отмена</a>
    """
    return HTMLResponse(content=html)

@router.post("/edit/{audience_id}", response_model=None)
async def edit_audience(
    request: Request,
    audience_id: int,
    name: str = Form(...),
    building_id: int = Form(None),
    capacity: int = Form(None),
    type: str = Form(None),
    is_active: bool = Form(True),
    db: AsyncSession = Depends(get_db)
):
    data = AudienceUpdate(name=name, building_id=building_id, capacity=capacity, type=type, is_active=is_active)
    await audience_service.update_audience(db, audience_id, data)
    await log_action(db, "update_audience", {"id": audience_id, "name": name, "building_id": building_id, "capacity": capacity, "type": type, "is_active": is_active}, request)
    return RedirectResponse(url="/admin/audiences", status_code=303)

@router.get("/delete/{audience_id}", response_class=HTMLResponse)
async def confirm_delete_audience(audience_id: int, db: AsyncSession = Depends(get_db)):
    audience = await audience_service.get_audience(db, audience_id)
    if not audience:
        return HTMLResponse("Аудитория не найдена", status_code=404)
    if await has_dependent_audience_subjects(db, audience_id):
        html = f"""
        <h1>Ошибка удаления аудитории "{audience.name}"</h1>
        <p>Невозможно удалить аудиторию, так как она связана с предметами. Сначала удалите эти связи.</p>
        <a href="/admin/audiences">Вернуться к списку аудиторий</a>
        """
        return HTMLResponse(content=html, status_code=400)
    html = f"""
    <h1>Удалить аудиторию "{audience.name}"?</h1>
    <form method="post" action="/admin/audiences/delete/{audience_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/audiences">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/delete/{audience_id}", response_model=None)
async def delete_audience(
    request: Request,
    audience_id: int,
    db: AsyncSession = Depends(get_db)
):
    await audience_service.delete_audience(db, audience_id)
    await log_action(db, "delete_audience", {"id": audience_id}, request)
    return RedirectResponse(url="/admin/audiences", status_code=303)

@router.post("/bulk-delete", response_model=None)
async def bulk_delete_audiences(
    request: Request,
    ids: List[int] = Form(...),
    db: AsyncSession = Depends(get_db)
):
    forbidden = []
    for aid in ids:
        if await has_dependent_audience_subjects(db, aid):
            forbidden.append(aid)
    if forbidden:
        html = f"""
        <h1>Ошибка массового удаления</h1>
        <p>Следующие аудитории имеют связи с предметами и не могут быть удалены: {forbidden}</p>
        <a href="/admin/audiences">Вернуться к списку аудиторий</a>
        """
        return HTMLResponse(content=html, status_code=400)
    await audience_service.bulk_delete_audiences(db, ids)
    await log_action(db, "bulk_delete_audiences", {"ids": ids}, request)
    return RedirectResponse(url="/admin/audiences", status_code=303)

@router.get("/export")
async def export_audiences(db: AsyncSession = Depends(get_db)):
    audiences = await audience_service.get_all_audiences(db)
    buildings = await building_service.get_all_buildings(db)
    b_dict = {b.id: b.name for b in buildings}
    data = [{"ID": a.id, "Название": a.name, "Здание ID": a.building_id, "Здание": b_dict.get(a.building_id, ""), "Вместимость": a.capacity, "Тип": a.type or "", "Активна": "Да" if a.is_active else "Нет"} for a in audiences]
    return export_to_excel(data, ["ID", "Название", "Здание ID", "Здание", "Вместимость", "Тип", "Активна"], "Аудитории", "audiences.xlsx")