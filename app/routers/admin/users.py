from typing import List
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import user as user_service
from app.services import user_type as user_type_service
from app.schemas.user import UserCreate, UserUpdate
from app.routers.admin.common import export_to_excel, _common_styles, _import_script
from app.services.audit import log_action

router = APIRouter(prefix="/admin/users", tags=["Admin Users"])

def render_users_html(users, user_types):
    html = f"<h1>Пользователи</h1>{_common_styles()}"
    html += "<div><a href='/admin/users/export' class='btn-excel'>📎 Экспорт в Excel</a>"
    html += " <button onclick='toggleImportForm_users()' class='btn-excel btn-import'>📂 Импорт из Excel</button></div>"
    html += f"<div id='importForm_users' class='import-form'>"
    html += f"<form id='uploadForm_users' action='/admin/import/users' method='post' enctype='multipart/form-data'>"
    html += "<input type='file' name='file' accept='.xlsx,.xls' required>"
    html += "<button type='submit'>Загрузить</button>"
    html += "<button type='button' onclick='toggleImportForm_users()'>Отмена</button>"
    html += "</form></div>"
    html += _import_script("users")
    html += "<form method='post' action='/admin/users/add'>"
    html += "<input type='text' name='username' placeholder='Логин' required>"
    html += "<input type='email' name='email' placeholder='Email' required>"
    html += "<input type='password' name='password' placeholder='Пароль' required>"
    html += "<input type='text' name='full_name' placeholder='ФИО'>"
    html += "<select name='user_type_id'><option value=''>Тип пользователя</option>"
    for ut in user_types:
        html += f"<option value='{ut.id}'>{ut.name}</option>"
    html += "</select>"
    html += "<label><input type='checkbox' name='is_active' value='true' checked> Активен</label>"
    html += "<button type='submit'>Добавить</button>"
    html += "</form>"
    html += "<form method='post' action='/admin/users/bulk-delete' onsubmit='return confirmDeleteSelected();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllUsers'> Выделить всё</label>"
    html += "<ul>"
    for u in users:
        html += f"<li><input type='checkbox' name='ids' value='{u.id}'> "
        html += f"{u.username} ({u.email}) – {u.full_name or '—'}"
        if u.user_type:
            html += f" [{u.user_type.name}]"
        html += f" <a href='/admin/users/edit/{u.id}'>Редактировать</a> "
        html += f"<a href='/admin/users/delete/{u.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<a href='/admin/'>На главную админки</a>"
    html += """
    <script>
        const selectAll = document.getElementById('selectAllUsers');
        if(selectAll) selectAll.addEventListener('change', function() {
            document.querySelectorAll('input[name="ids"]').forEach(cb => cb.checked = selectAll.checked);
        });
        function confirmDeleteSelected() {
            const anyChecked = document.querySelectorAll('input[name="ids"]:checked').length > 0;
            if (!anyChecked) { alert('Не выбрано ни одной записи'); return false; }
            return confirm('Удалить выбранных пользователей?');
        }
    </script>
    """
    return html

@router.get("", response_class=HTMLResponse)
async def users_page(db: AsyncSession = Depends(get_db)):
    users = await user_service.get_all_users(db)
    user_types = await user_type_service.get_all_user_types(db)
    return HTMLResponse(content=render_users_html(users, user_types))

@router.post("/add", response_model=None)
async def add_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(None),
    user_type_id: int = Form(None),
    is_active: bool = Form(True),
    db: AsyncSession = Depends(get_db)
):
    data = UserCreate(username=username, email=email, password=password, full_name=full_name, user_type_id=user_type_id, is_active=is_active)
    user = await user_service.create_user(db, data)
    await log_action(db, "create_user", {"id": user.id, "username": username, "email": email, "full_name": full_name, "user_type_id": user_type_id, "is_active": is_active}, request)
    return RedirectResponse(url="/admin/users", status_code=303)

@router.get("/edit/{user_id}", response_class=HTMLResponse)
async def edit_user_form(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await user_service.get_user(db, user_id)
    if not user:
        return HTMLResponse("Пользователь не найден", status_code=404)
    user_types = await user_type_service.get_all_user_types(db)
    html = f"""
    <h1>Редактировать пользователя {user.username}</h1>
    <form method="post" action="/admin/users/edit/{user_id}">
        <input type="text" name="username" value="{user.username}" required>
        <input type="email" name="email" value="{user.email}" required>
        <input type="password" name="password" placeholder="Новый пароль (оставьте пустым, чтобы не менять)">
        <input type="text" name="full_name" value="{user.full_name or ''}">
        <select name="user_type_id">
            <option value="">Тип пользователя</option>
    """
    for ut in user_types:
        selected = "selected" if ut.id == user.user_type_id else ""
        html += f'<option value="{ut.id}" {selected}>{ut.name}</option>'
    html += f"""
        </select>
        <label><input type="checkbox" name="is_active" value="true" {'checked' if user.is_active else ''}> Активен</label>
        <button type="submit">Сохранить</button>
    </form>
    <a href="/admin/users">Отмена</a>
    """
    return HTMLResponse(content=html)

@router.post("/edit/{user_id}", response_model=None)
async def edit_user(
    request: Request,
    user_id: int,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(None),
    full_name: str = Form(None),
    user_type_id: int = Form(None),
    is_active: bool = Form(True),
    db: AsyncSession = Depends(get_db)
):
    data = UserUpdate(username=username, email=email, password=password if password else None, full_name=full_name, user_type_id=user_type_id, is_active=is_active)
    await user_service.update_user(db, user_id, data)
    await log_action(db, "update_user", {"id": user_id, "username": username, "email": email, "full_name": full_name, "user_type_id": user_type_id, "is_active": is_active}, request)
    return RedirectResponse(url="/admin/users", status_code=303)

@router.get("/delete/{user_id}", response_class=HTMLResponse)
async def confirm_delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await user_service.get_user(db, user_id)
    if not user:
        return HTMLResponse("Пользователь не найден", status_code=404)
    html = f"""
    <h1>Удалить пользователя "{user.username}"?</h1>
    <form method="post" action="/admin/users/delete/{user_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/users">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/delete/{user_id}", response_model=None)
async def delete_user(
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    await user_service.delete_user(db, user_id)
    await log_action(db, "delete_user", {"id": user_id}, request)
    return RedirectResponse(url="/admin/users", status_code=303)

@router.post("/bulk-delete", response_model=None)
async def bulk_delete_users(
    request: Request,
    ids: List[int] = Form(...),
    db: AsyncSession = Depends(get_db)
):
    await user_service.bulk_delete_users(db, ids)
    await log_action(db, "bulk_delete_users", {"ids": ids}, request)
    return RedirectResponse(url="/admin/users", status_code=303)

@router.get("/export")
async def export_users(db: AsyncSession = Depends(get_db)):
    users = await user_service.get_all_users(db)
    data = [{"ID": u.id, "Логин": u.username, "Email": u.email, "ФИО": u.full_name or "", "Тип пользователя ID": u.user_type_id, "Активен": "Да" if u.is_active else "Нет", "Дата создания": u.created_at, "Последний вход": u.last_login} for u in users]
    return export_to_excel(data, ["ID", "Логин", "Email", "ФИО", "Тип пользователя ID", "Активен", "Дата создания", "Последний вход"], "Пользователи", "users.xlsx")