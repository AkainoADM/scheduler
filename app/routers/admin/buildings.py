from typing import List
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import building as building_service
from app.schemas.building import BuildingCreate, BuildingUpdate
from app.routers.admin.common import export_to_excel, _common_styles, _import_script, has_dependent_audiences
from app.services.audit import log_action

router = APIRouter(prefix="/admin/buildings", tags=["Admin Buildings"])

def render_buildings_html(buildings):
    html = f"<h1>Здания</h1>{_common_styles()}"
    html += "<div><a href='/admin/buildings/export' class='btn-excel'>📎 Экспорт в Excel</a>"
    html += " <button onclick='toggleImportForm_buildings()' class='btn-excel btn-import'>📂 Импорт из Excel</button></div>"
    html += f"<div id='importForm_buildings' class='import-form'>"
    html += f"<form id='uploadForm_buildings' action='/admin/import/buildings' method='post' enctype='multipart/form-data'>"
    html += "<input type='file' name='file' accept='.xlsx,.xls' required>"
    html += "<button type='submit'>Загрузить</button>"
    html += "<button type='button' onclick='toggleImportForm_buildings()'>Отмена</button>"
    html += "</form></div>"
    html += _import_script("buildings")
    html += "<form method='post' action='/admin/buildings/add'>"
    html += "<input type='text' name='name' placeholder='Название здания' required>"
    html += "<input type='text' name='address' placeholder='Адрес'>"
    html += "<button type='submit'>Добавить</button>"
    html += "</form>"
    html += "<form method='post' action='/admin/buildings/bulk-delete' onsubmit='return confirmDeleteSelected();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllBuildings'> Выделить всё</label>"
    html += "<ul>"
    for b in buildings:
        html += f"<li><input type='checkbox' name='ids' value='{b.id}'> "
        html += f"{b.name} (Адрес: {b.address or 'не указан'}) "
        html += f"<a href='/admin/buildings/edit/{b.id}'>Редактировать</a> "
        html += f"<a href='/admin/buildings/delete/{b.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<a href='/admin/'>На главную админки</a>"
    html += """
    <script>
        const selectAll = document.getElementById('selectAllBuildings');
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
async def buildings_page(db: AsyncSession = Depends(get_db)):
    buildings = await building_service.get_all_buildings(db)
    return HTMLResponse(content=render_buildings_html(buildings))

@router.post("/add", response_model=None)
async def add_building(
    request: Request,
    name: str = Form(...),
    address: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = BuildingCreate(name=name, address=address)
    building = await building_service.create_building(db, data)
    await log_action(db, "create_building", {"id": building.id, "name": name, "address": address}, request)
    return RedirectResponse(url="/admin/buildings", status_code=303)

@router.get("/edit/{building_id}", response_class=HTMLResponse)
async def edit_building_form(building_id: int, db: AsyncSession = Depends(get_db)):
    building = await building_service.get_building(db, building_id)
    if not building:
        return HTMLResponse("Здание не найдено", status_code=404)
    html = f"""
    <h1>Редактировать здание</h1>
    <form method="post" action="/admin/buildings/edit/{building_id}">
        <input type="text" name="name" value="{building.name}" required>
        <input type="text" name="address" value="{building.address or ''}">
        <button type="submit">Сохранить</button>
    </form>
    <a href="/admin/buildings">Отмена</a>
    """
    return HTMLResponse(content=html)

@router.post("/edit/{building_id}", response_model=None)
async def edit_building(
    request: Request,
    building_id: int,
    name: str = Form(...),
    address: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = BuildingUpdate(name=name, address=address)
    await building_service.update_building(db, building_id, data)
    await log_action(db, "update_building", {"id": building_id, "name": name, "address": address}, request)
    return RedirectResponse(url="/admin/buildings", status_code=303)

@router.get("/delete/{building_id}", response_class=HTMLResponse)
async def confirm_delete_building(building_id: int, db: AsyncSession = Depends(get_db)):
    building = await building_service.get_building(db, building_id)
    if not building:
        return HTMLResponse("Здание не найдено", status_code=404)
    if await has_dependent_audiences(db, building_id):
        html = f"""
        <h1>Ошибка удаления здания "{building.name}"</h1>
        <p>Невозможно удалить здание, так как к нему привязаны аудитории. Сначала удалите или переназначьте аудитории.</p>
        <a href="/admin/buildings">Вернуться к списку зданий</a>
        """
        return HTMLResponse(content=html, status_code=400)
    html = f"""
    <h1>Удалить здание "{building.name}"?</h1>
    <form method="post" action="/admin/buildings/delete/{building_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/buildings">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/delete/{building_id}", response_model=None)
async def delete_building(
    request: Request,
    building_id: int,
    db: AsyncSession = Depends(get_db)
):
    await building_service.delete_building(db, building_id)
    await log_action(db, "delete_building", {"id": building_id}, request)
    return RedirectResponse(url="/admin/buildings", status_code=303)

@router.post("/bulk-delete", response_model=None)
async def bulk_delete_buildings(
    request: Request,
    ids: List[int] = Form(...),
    db: AsyncSession = Depends(get_db)
):
    forbidden = []
    for bid in ids:
        if await has_dependent_audiences(db, bid):
            forbidden.append(bid)
    if forbidden:
        html = f"""
        <h1>Ошибка массового удаления</h1>
        <p>Следующие здания имеют привязанные аудитории и не могут быть удалены: {forbidden}</p>
        <a href="/admin/buildings">Вернуться к списку зданий</a>
        """
        return HTMLResponse(content=html, status_code=400)
    await building_service.bulk_delete_buildings(db, ids)
    await log_action(db, "bulk_delete_buildings", {"ids": ids}, request)
    return RedirectResponse(url="/admin/buildings", status_code=303)

@router.get("/export")
async def export_buildings(db: AsyncSession = Depends(get_db)):
    buildings = await building_service.get_all_buildings(db)
    data = [{"ID": b.id, "Название": b.name, "Адрес": b.address or ""} for b in buildings]
    return export_to_excel(data, ["ID", "Название", "Адрес"], "Здания", "buildings.xlsx")