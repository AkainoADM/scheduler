from typing import List
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import permission as permission_service
from app.schemas.permission import PermissionCreate, PermissionUpdate
from app.routers.admin.common import export_to_excel, _common_styles, _import_script
from app.services.audit import log_action

router = APIRouter(prefix="/admin/permissions", tags=["Admin Permissions"])

def render_permissions_html(permissions):
    html = f"<h1>Права</h1>{_common_styles()}"
    html += "<div><a href='/admin/permissions/export' class='btn-excel'>📎 Экспорт в Excel</a>"
    html += " <button onclick='toggleImportForm_permissions()' class='btn-excel btn-import'>📂 Импорт из Excel</button></div>"
    html += f"<div id='importForm_permissions' class='import-form'>"
    html += f"<form id='uploadForm_permissions' action='/admin/import/permissions' method='post' enctype='multipart/form-data'>"
    html += "<input type='file' name='file' accept='.xlsx,.xls' required>"
    html += "<button type='submit'>Загрузить</button>"
    html += "<button type='button' onclick='toggleImportForm_permissions()'>Отмена</button>"
    html += "</form></div>"
    html += _import_script("permissions")
    html += "<form method='post' action='/admin/permissions/add'>"
    html += "<input type='text' name='permission_code' placeholder='Код права' required>"
    html += "<input type='text' name='permission_name' placeholder='Название' required>"
    html += "<input type='text' name='description' placeholder='Описание'>"
    html += "<button type='submit'>Добавить</button>"
    html += "</form>"
    html += "<form method='post' action='/admin/permissions/bulk-delete' onsubmit='return confirmDeleteSelected();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllPermissions'> Выделить всё</label>"
    html += "<ul>"
    for p in permissions:
        html += f"<li><input type='checkbox' name='ids' value='{p.id}'> "
        html += f"{p.permission_name} (код: {p.permission_code})"
        if p.description:
            html += f" – {p.description}"
        html += f" <a href='/admin/permissions/edit/{p.id}'>Редактировать</a> "
        html += f"<a href='/admin/permissions/delete/{p.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<a href='/admin/'>На главную админки</a>"
    html += """
    <script>
        const selectAll = document.getElementById('selectAllPermissions');
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
async def permissions_page(db: AsyncSession = Depends(get_db)):
    permissions = await permission_service.get_all_permissions(db)
    return HTMLResponse(content=render_permissions_html(permissions))

@router.post("/add", response_model=None)
async def add_permission(
    request: Request,
    permission_code: str = Form(...),
    permission_name: str = Form(...),
    description: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = PermissionCreate(permission_code=permission_code, permission_name=permission_name, description=description)
    perm = await permission_service.create_permission(db, data)
    await log_action(db, "create_permission", {"id": perm.id, "permission_code": permission_code, "permission_name": permission_name, "description": description}, request)
    return RedirectResponse(url="/admin/permissions", status_code=303)

@router.get("/edit/{perm_id}", response_class=HTMLResponse)
async def edit_permission_form(perm_id: int, db: AsyncSession = Depends(get_db)):
    perm = await permission_service.get_permission(db, perm_id)
    if not perm:
        return HTMLResponse("Право не найдено", status_code=404)
    html = f"""
    <h1>Редактировать право</h1>
    <form method="post" action="/admin/permissions/edit/{perm_id}">
        <input type="text" name="permission_code" value="{perm.permission_code}" required>
        <input type="text" name="permission_name" value="{perm.permission_name}" required>
        <input type="text" name="description" value="{perm.description or ''}">
        <button type="submit">Сохранить</button>
    </form>
    <a href="/admin/permissions">Отмена</a>
    """
    return HTMLResponse(content=html)

@router.post("/edit/{perm_id}", response_model=None)
async def edit_permission(
    request: Request,
    perm_id: int,
    permission_code: str = Form(...),
    permission_name: str = Form(...),
    description: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = PermissionUpdate(permission_code=permission_code, permission_name=permission_name, description=description)
    await permission_service.update_permission(db, perm_id, data)
    await log_action(db, "update_permission", {"id": perm_id, "permission_code": permission_code, "permission_name": permission_name, "description": description}, request)
    return RedirectResponse(url="/admin/permissions", status_code=303)

@router.get("/delete/{perm_id}", response_class=HTMLResponse)
async def confirm_delete_permission(perm_id: int, db: AsyncSession = Depends(get_db)):
    perm = await permission_service.get_permission(db, perm_id)
    if not perm:
        return HTMLResponse("Право не найдено", status_code=404)
    html = f"""
    <h1>Удалить право "{perm.permission_name}"?</h1>
    <form method="post" action="/admin/permissions/delete/{perm_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/permissions">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/delete/{perm_id}", response_model=None)
async def delete_permission(
    request: Request,
    perm_id: int,
    db: AsyncSession = Depends(get_db)
):
    await permission_service.delete_permission(db, perm_id)
    await log_action(db, "delete_permission", {"id": perm_id}, request)
    return RedirectResponse(url="/admin/permissions", status_code=303)

@router.post("/bulk-delete", response_model=None)
async def bulk_delete_permissions(
    request: Request,
    ids: List[int] = Form(...),
    db: AsyncSession = Depends(get_db)
):
    await permission_service.bulk_delete_permissions(db, ids)
    await log_action(db, "bulk_delete_permissions", {"ids": ids}, request)
    return RedirectResponse(url="/admin/permissions", status_code=303)

@router.get("/export")
async def export_permissions(db: AsyncSession = Depends(get_db)):
    perms = await permission_service.get_all_permissions(db)
    data = [{"ID": p.id, "Код": p.permission_code, "Название": p.permission_name, "Описание": p.description or ""} for p in perms]
    return export_to_excel(data, ["ID", "Код", "Название", "Описание"], "Права", "permissions.xlsx")