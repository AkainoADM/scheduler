from typing import List
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import subdivision as subdivision_service
from app.schemas.subdivision import SubdivisionCreate, SubdivisionUpdate
from app.routers.admin.common import export_to_excel, _common_styles, _import_script
from app.services.audit import log_action

router = APIRouter(prefix="/admin/subdivisions", tags=["Admin Subdivisions"])

def render_subdivisions_html(subdivisions):
    html = f"<h1>Подразделения</h1>{_common_styles()}"
    html += "<div><a href='/admin/subdivisions/export' class='btn-excel'>📎 Экспорт в Excel</a>"
    html += " <button onclick='toggleImportForm_subdivisions()' class='btn-excel btn-import'>📂 Импорт из Excel</button></div>"
    html += f"<div id='importForm_subdivisions' class='import-form'>"
    html += f"<form id='uploadForm_subdivisions' action='/admin/import/subdivisions' method='post' enctype='multipart/form-data'>"
    html += "<input type='file' name='file' accept='.xlsx,.xls' required>"
    html += "<button type='submit'>Загрузить</button>"
    html += "<button type='button' onclick='toggleImportForm_subdivisions()'>Отмена</button>"
    html += "</form></div>"
    html += _import_script("subdivisions")
    html += "<form method='post' action='/admin/subdivisions/add'>"
    html += "<input type='text' name='name' placeholder='Название' required>"
    html += "<button type='submit'>Добавить</button>"
    html += "</form>"
    html += "<form method='post' action='/admin/subdivisions/bulk-delete' onsubmit='return confirmDeleteSelected();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllSubdivisions'> Выделить всё</label>"
    html += "<ul>"
    for s in subdivisions:
        html += f"<li><input type='checkbox' name='ids' value='{s.id}'> "
        html += f"{s.name}"
        html += f" <a href='/admin/subdivisions/edit/{s.id}'>Редактировать</a> "
        html += f"<a href='/admin/subdivisions/delete/{s.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<a href='/admin/'>На главную админки</a>"
    html += """
    <script>
        const selectAll = document.getElementById('selectAllSubdivisions');
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
async def subdivisions_page(db: AsyncSession = Depends(get_db)):
    subdivisions = await subdivision_service.get_all_subdivisions(db)
    return HTMLResponse(content=render_subdivisions_html(subdivisions))

@router.post("/add", response_model=None)
async def add_subdivision(
    request: Request,
    name: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    data = SubdivisionCreate(name=name)
    sub = await subdivision_service.create_subdivision(db, data)
    await log_action(db, "create_subdivision", {"id": sub.id, "name": name}, request)
    return RedirectResponse(url="/admin/subdivisions", status_code=303)

@router.get("/edit/{sub_id}", response_class=HTMLResponse)
async def edit_subdivision_form(sub_id: int, db: AsyncSession = Depends(get_db)):
    sub = await subdivision_service.get_subdivision(db, sub_id)
    if not sub:
        return HTMLResponse("Подразделение не найдено", status_code=404)
    html = f"""
    <h1>Редактировать подразделение</h1>
    <form method="post" action="/admin/subdivisions/edit/{sub_id}">
        <input type="text" name="name" value="{sub.name}" required>
        <button type="submit">Сохранить</button>
    </form>
    <a href="/admin/subdivisions">Отмена</a>
    """
    return HTMLResponse(content=html)

@router.post("/edit/{sub_id}", response_model=None)
async def edit_subdivision(
    request: Request,
    sub_id: int,
    name: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    data = SubdivisionUpdate(name=name)
    await subdivision_service.update_subdivision(db, sub_id, data)
    await log_action(db, "update_subdivision", {"id": sub_id, "name": name}, request)
    return RedirectResponse(url="/admin/subdivisions", status_code=303)

@router.get("/delete/{sub_id}", response_class=HTMLResponse)
async def confirm_delete_subdivision(sub_id: int, db: AsyncSession = Depends(get_db)):
    sub = await subdivision_service.get_subdivision(db, sub_id)
    if not sub:
        return HTMLResponse("Подразделение не найдено", status_code=404)
    html = f"""
    <h1>Удалить подразделение "{sub.name}"?</h1>
    <form method="post" action="/admin/subdivisions/delete/{sub_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/subdivisions">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/delete/{sub_id}", response_model=None)
async def delete_subdivision(
    request: Request,
    sub_id: int,
    db: AsyncSession = Depends(get_db)
):
    await subdivision_service.delete_subdivision(db, sub_id)
    await log_action(db, "delete_subdivision", {"id": sub_id}, request)
    return RedirectResponse(url="/admin/subdivisions", status_code=303)

@router.post("/bulk-delete", response_model=None)
async def bulk_delete_subdivisions(
    request: Request,
    ids: List[int] = Form(...),
    db: AsyncSession = Depends(get_db)
):
    await subdivision_service.bulk_delete_subdivisions(db, ids)
    await log_action(db, "bulk_delete_subdivisions", {"ids": ids}, request)
    return RedirectResponse(url="/admin/subdivisions", status_code=303)

@router.get("/export")
async def export_subdivisions(db: AsyncSession = Depends(get_db)):
    subs = await subdivision_service.get_all_subdivisions(db)
    data = [{"ID": s.id, "Название": s.name} for s in subs]
    return export_to_excel(data, ["ID", "Название"], "Подразделения", "subdivisions.xlsx")