from typing import List
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import role as role_service
from app.schemas.role import RoleCreate, RoleUpdate
from app.routers.admin.common import export_to_excel, _common_styles, _import_script
from app.services.audit import log_action

router = APIRouter(prefix="/admin/roles", tags=["Admin Roles"])

def render_roles_html(roles):
    html = f"<h1>Роли</h1>{_common_styles()}"
    html += "<div><a href='/admin/roles/export' class='btn-excel'>📎 Экспорт в Excel</a>"
    html += " <button onclick='toggleImportForm_roles()' class='btn-excel btn-import'>📂 Импорт из Excel</button></div>"
    html += f"<div id='importForm_roles' class='import-form'>"
    html += f"<form id='uploadForm_roles' action='/admin/import/roles' method='post' enctype='multipart/form-data'>"
    html += "<input type='file' name='file' accept='.xlsx,.xls' required>"
    html += "<button type='submit'>Загрузить</button>"
    html += "<button type='button' onclick='toggleImportForm_roles()'>Отмена</button>"
    html += "</form></div>"
    html += _import_script("roles")
    html += "<form method='post' action='/admin/roles/add'>"
    html += "<input type='text' name='role_name' placeholder='Название роли' required>"
    html += "<input type='text' name='description' placeholder='Описание'>"
    html += "<button type='submit'>Добавить</button>"
    html += "</form>"
    html += "<form method='post' action='/admin/roles/bulk-delete' onsubmit='return confirmDeleteSelected();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllRoles'> Выделить всё</label>"
    html += "<ul>"
    for r in roles:
        html += f"<li><input type='checkbox' name='ids' value='{r.id}'> "
        html += f"{r.role_name}"
        if r.description:
            html += f" – {r.description}"
        html += f" <a href='/admin/roles/edit/{r.id}'>Редактировать</a> "
        html += f"<a href='/admin/roles/delete/{r.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<a href='/admin/'>На главную админки</a>"
    html += """
    <script>
        const selectAll = document.getElementById('selectAllRoles');
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
async def roles_page(db: AsyncSession = Depends(get_db)):
    roles = await role_service.get_all_roles(db)
    return HTMLResponse(content=render_roles_html(roles))

@router.post("/add", response_model=None)
async def add_role(
    request: Request,
    role_name: str = Form(...),
    description: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = RoleCreate(role_name=role_name, description=description)
    role = await role_service.create_role(db, data)
    await log_action(db, "create_role", {"id": role.id, "role_name": role_name, "description": description}, request)
    return RedirectResponse(url="/admin/roles", status_code=303)

@router.get("/edit/{role_id}", response_class=HTMLResponse)
async def edit_role_form(role_id: int, db: AsyncSession = Depends(get_db)):
    role = await role_service.get_role(db, role_id)
    if not role:
        return HTMLResponse("Роль не найдена", status_code=404)
    html = f"""
    <h1>Редактировать роль</h1>
    <form method="post" action="/admin/roles/edit/{role_id}">
        <input type="text" name="role_name" value="{role.role_name}" required>
        <input type="text" name="description" value="{role.description or ''}">
        <button type="submit">Сохранить</button>
    </form>
    <a href="/admin/roles">Отмена</a>
    """
    return HTMLResponse(content=html)

@router.post("/edit/{role_id}", response_model=None)
async def edit_role(
    request: Request,
    role_id: int,
    role_name: str = Form(...),
    description: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = RoleUpdate(role_name=role_name, description=description)
    await role_service.update_role(db, role_id, data)
    await log_action(db, "update_role", {"id": role_id, "role_name": role_name, "description": description}, request)
    return RedirectResponse(url="/admin/roles", status_code=303)

@router.get("/delete/{role_id}", response_class=HTMLResponse)
async def confirm_delete_role(role_id: int, db: AsyncSession = Depends(get_db)):
    role = await role_service.get_role(db, role_id)
    if not role:
        return HTMLResponse("Роль не найдена", status_code=404)
    html = f"""
    <h1>Удалить роль "{role.role_name}"?</h1>
    <form method="post" action="/admin/roles/delete/{role_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/roles">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/delete/{role_id}", response_model=None)
async def delete_role(
    request: Request,
    role_id: int,
    db: AsyncSession = Depends(get_db)
):
    await role_service.delete_role(db, role_id)
    await log_action(db, "delete_role", {"id": role_id}, request)
    return RedirectResponse(url="/admin/roles", status_code=303)

@router.post("/bulk-delete", response_model=None)
async def bulk_delete_roles(
    request: Request,
    ids: List[int] = Form(...),
    db: AsyncSession = Depends(get_db)
):
    await role_service.bulk_delete_roles(db, ids)
    await log_action(db, "bulk_delete_roles", {"ids": ids}, request)
    return RedirectResponse(url="/admin/roles", status_code=303)

@router.get("/export")
async def export_roles(db: AsyncSession = Depends(get_db)):
    roles = await role_service.get_all_roles(db)
    data = [{"ID": r.id, "Название": r.role_name, "Описание": r.description or ""} for r in roles]
    return export_to_excel(data, ["ID", "Название", "Описание"], "Роли", "roles.xlsx")