from typing import List
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import user_type as user_type_service
from app.schemas.user_type import UserTypeCreate, UserTypeUpdate
from app.routers.admin.common import export_to_excel, _common_styles, _import_script
from app.services.audit import log_action

router = APIRouter(prefix="/admin/user-types", tags=["Admin User Types"])

def render_user_types_html(user_types):
    html = f"<h1>Типы пользователей</h1>{_common_styles()}"
    html += "<div><a href='/admin/user-types/export' class='btn-excel'>📎 Экспорт в Excel</a>"
    html += " <button onclick='toggleImportForm_user_types()' class='btn-excel btn-import'>📂 Импорт из Excel</button></div>"
    html += f"<div id='importForm_user_types' class='import-form'>"
    html += f"<form id='uploadForm_user_types' action='/admin/import/user_types' method='post' enctype='multipart/form-data'>"
    html += "<input type='file' name='file' accept='.xlsx,.xls' required>"
    html += "<button type='submit'>Загрузить</button>"
    html += "<button type='button' onclick='toggleImportForm_user_types()'>Отмена</button>"
    html += "</form></div>"
    html += _import_script("user_types")
    html += "<form method='post' action='/admin/user-types/bulk-delete' onsubmit='return confirmDeleteSelected();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllUserTypes'> Выделить всё</label>"
    html += "<ul>"
    for ut in user_types:
        html += f"<li><input type='checkbox' name='ids' value='{ut.id}'> "
        html += f"{ut.name} (код: {ut.code})"
        if ut.description:
            html += f" – {ut.description}"
        html += f" <a href='/admin/user-types/edit/{ut.id}'>Редактировать</a> "
        html += f"<a href='/admin/user-types/delete/{ut.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<form method='post' action='/admin/user-types/add' style='margin-top: 20px;'>"
    html += "<input type='text' name='code' placeholder='Код (например, teacher)' required>"
    html += "<input type='text' name='name' placeholder='Название' required>"
    html += "<input type='text' name='description' placeholder='Описание'>"
    html += "<button type='submit'>Добавить</button>"
    html += "</form>"
    html += "<a href='/admin/'>На главную админки</a>"
    html += """
    <script>
        const selectAll = document.getElementById('selectAllUserTypes');
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
async def user_types_page(db: AsyncSession = Depends(get_db)):
    user_types = await user_type_service.get_all_user_types(db)
    return HTMLResponse(content=render_user_types_html(user_types))

@router.post("/add", response_model=None)
async def add_user_type(
    request: Request,
    code: str = Form(...),
    name: str = Form(...),
    description: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = UserTypeCreate(code=code, name=name, description=description)
    ut = await user_type_service.create_user_type(db, data)
    await log_action(db, "create_user_type", {"id": ut.id, "code": code, "name": name, "description": description}, request)
    return RedirectResponse(url="/admin/user-types", status_code=303)

@router.get("/edit/{ut_id}", response_class=HTMLResponse)
async def edit_user_type_form(ut_id: int, db: AsyncSession = Depends(get_db)):
    ut = await user_type_service.get_user_type(db, ut_id)
    if not ut:
        return HTMLResponse("Тип пользователя не найден", status_code=404)
    html = f"""
    <h1>Редактировать тип пользователя</h1>
    <form method="post" action="/admin/user-types/edit/{ut_id}">
        <input type="text" name="code" value="{ut.code}" required>
        <input type="text" name="name" value="{ut.name}" required>
        <input type="text" name="description" value="{ut.description or ''}">
        <button type="submit">Сохранить</button>
    </form>
    <a href="/admin/user-types">Отмена</a>
    """
    return HTMLResponse(content=html)

@router.post("/edit/{ut_id}", response_model=None)
async def edit_user_type(
    request: Request,
    ut_id: int,
    code: str = Form(...),
    name: str = Form(...),
    description: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = UserTypeUpdate(code=code, name=name, description=description)
    await user_type_service.update_user_type(db, ut_id, data)
    await log_action(db, "update_user_type", {"id": ut_id, "code": code, "name": name, "description": description}, request)
    return RedirectResponse(url="/admin/user-types", status_code=303)

@router.get("/delete/{ut_id}", response_class=HTMLResponse)
async def confirm_delete_user_type(ut_id: int, db: AsyncSession = Depends(get_db)):
    ut = await user_type_service.get_user_type(db, ut_id)
    if not ut:
        return HTMLResponse("Тип пользователя не найден", status_code=404)
    html = f"""
    <h1>Удалить тип "{ut.name}"?</h1>
    <form method="post" action="/admin/user-types/delete/{ut_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/user-types">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/delete/{ut_id}", response_model=None)
async def delete_user_type(
    request: Request,
    ut_id: int,
    db: AsyncSession = Depends(get_db)
):
    await user_type_service.delete_user_type(db, ut_id)
    await log_action(db, "delete_user_type", {"id": ut_id}, request)
    return RedirectResponse(url="/admin/user-types", status_code=303)

@router.post("/bulk-delete", response_model=None)
async def bulk_delete_user_types(
    request: Request,
    ids: List[int] = Form(...),
    db: AsyncSession = Depends(get_db)
):
    await user_type_service.bulk_delete_user_types(db, ids)
    await log_action(db, "bulk_delete_user_types", {"ids": ids}, request)
    return RedirectResponse(url="/admin/user-types", status_code=303)

@router.get("/export")
async def export_user_types(db: AsyncSession = Depends(get_db)):
    types = await user_type_service.get_all_user_types(db)
    data = [{"ID": t.id, "Код": t.code, "Название": t.name, "Описание": t.description or ""} for t in types]
    return export_to_excel(data, ["ID", "Код", "Название", "Описание"], "Типы пользователей", "user_types.xlsx")