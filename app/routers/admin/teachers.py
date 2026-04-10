from typing import List
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import teacher as teacher_service
from app.schemas.teacher import TeacherCreate, TeacherUpdate
from app.routers.admin.common import export_to_excel, _common_styles, _import_script, has_dependent_teacher_groups, has_dependent_teacher_subjects
from app.services.audit import log_action

router = APIRouter(prefix="/admin/teachers", tags=["Admin Teachers"])

def render_teachers_html(teachers):
    html = f"<h1>Преподаватели</h1>{_common_styles()}"
    html += "<div><a href='/admin/teachers/export' class='btn-excel'>📎 Экспорт в Excel</a>"
    html += " <button onclick='toggleImportForm_teachers()' class='btn-excel btn-import'>📂 Импорт из Excel</button></div>"
    html += f"<div id='importForm_teachers' class='import-form'>"
    html += f"<form id='uploadForm_teachers' action='/admin/import/teachers' method='post' enctype='multipart/form-data'>"
    html += "<input type='file' name='file' accept='.xlsx,.xls' required>"
    html += "<button type='submit'>Загрузить</button>"
    html += "<button type='button' onclick='toggleImportForm_teachers()'>Отмена</button>"
    html += "</form></div>"
    html += _import_script("teachers")
    html += "<form method='post' action='/admin/teachers/add'>"
    html += "<input type='text' name='login' placeholder='Логин' required>"
    html += "<input type='text' name='name' placeholder='ФИО' required>"
    html += "<input type='text' name='url' placeholder='Ссылка на страницу'>"
    html += "<button type='submit'>Добавить</button>"
    html += "</form>"
    html += "<form method='post' action='/admin/teachers/bulk-delete' onsubmit='return confirmDeleteSelected();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllTeachers'> Выделить всё</label>"
    html += "<ul>"
    for t in teachers:
        html += f"<li><input type='checkbox' name='ids' value='{t.id}'> "
        html += f"{t.name} (Логин: {t.login})"
        if t.url:
            html += f" – <a href='{t.url}'>страница</a>"
        html += f" <a href='/admin/teachers/edit/{t.id}'>Редактировать</a> "
        html += f"<a href='/admin/teachers/delete/{t.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<a href='/admin/'>На главную админки</a>"
    html += """
    <script>
        const selectAll = document.getElementById('selectAllTeachers');
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
async def teachers_page(db: AsyncSession = Depends(get_db)):
    teachers = await teacher_service.get_all_teachers(db)
    return HTMLResponse(content=render_teachers_html(teachers))

@router.post("/add", response_model=None)
async def add_teacher(
    request: Request,
    login: str = Form(...),
    name: str = Form(...),
    url: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = TeacherCreate(login=login, name=name, url=url)
    teacher = await teacher_service.create_teacher(db, data)
    await log_action(db, "create_teacher", {"id": teacher.id, "login": login, "name": name, "url": url}, request)
    return RedirectResponse(url="/admin/teachers", status_code=303)

@router.get("/edit/{teacher_id}", response_class=HTMLResponse)
async def edit_teacher_form(teacher_id: int, db: AsyncSession = Depends(get_db)):
    teacher = await teacher_service.get_teacher(db, teacher_id)
    if not teacher:
        return HTMLResponse("Преподаватель не найден", status_code=404)
    html = f"""
    <h1>Редактировать преподавателя</h1>
    <form method="post" action="/admin/teachers/edit/{teacher_id}">
        <input type="text" name="login" value="{teacher.login}" required>
        <input type="text" name="name" value="{teacher.name}" required>
        <input type="text" name="url" value="{teacher.url or ''}">
        <button type="submit">Сохранить</button>
    </form>
    <a href="/admin/teachers">Отмена</a>
    """
    return HTMLResponse(content=html)

@router.post("/edit/{teacher_id}", response_model=None)
async def edit_teacher(
    request: Request,
    teacher_id: int,
    login: str = Form(...),
    name: str = Form(...),
    url: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = TeacherUpdate(login=login, name=name, url=url)
    await teacher_service.update_teacher(db, teacher_id, data)
    await log_action(db, "update_teacher", {"id": teacher_id, "login": login, "name": name, "url": url}, request)
    return RedirectResponse(url="/admin/teachers", status_code=303)

@router.get("/delete/{teacher_id}", response_class=HTMLResponse)
async def confirm_delete_teacher(teacher_id: int, db: AsyncSession = Depends(get_db)):
    teacher = await teacher_service.get_teacher(db, teacher_id)
    if not teacher:
        return HTMLResponse("Преподаватель не найден", status_code=404)
    if await has_dependent_teacher_groups(db, teacher_id) or await has_dependent_teacher_subjects(db, teacher_id):
        html = f"""
        <h1>Ошибка удаления преподавателя "{teacher.name}"</h1>
        <p>Невозможно удалить преподавателя, так как он связан с группами или предметами. Сначала удалите эти связи.</p>
        <a href="/admin/teachers">Вернуться к списку преподавателей</a>
        """
        return HTMLResponse(content=html, status_code=400)
    html = f"""
    <h1>Удалить преподавателя "{teacher.name}"?</h1>
    <form method="post" action="/admin/teachers/delete/{teacher_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/teachers">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/delete/{teacher_id}", response_model=None)
async def delete_teacher(
    request: Request,
    teacher_id: int,
    db: AsyncSession = Depends(get_db)
):
    await teacher_service.delete_teacher(db, teacher_id)
    await log_action(db, "delete_teacher", {"id": teacher_id}, request)
    return RedirectResponse(url="/admin/teachers", status_code=303)

@router.post("/bulk-delete", response_model=None)
async def bulk_delete_teachers(
    request: Request,
    ids: List[int] = Form(...),
    db: AsyncSession = Depends(get_db)
):
    forbidden = []
    for tid in ids:
        if await has_dependent_teacher_groups(db, tid) or await has_dependent_teacher_subjects(db, tid):
            forbidden.append(tid)
    if forbidden:
        html = f"""
        <h1>Ошибка массового удаления</h1>
        <p>Следующие преподаватели имеют связи с группами или предметами и не могут быть удалены: {forbidden}</p>
        <a href="/admin/teachers">Вернуться к списку преподавателей</a>
        """
        return HTMLResponse(content=html, status_code=400)
    await teacher_service.bulk_delete_teachers(db, ids)
    await log_action(db, "bulk_delete_teachers", {"ids": ids}, request)
    return RedirectResponse(url="/admin/teachers", status_code=303)

@router.get("/export")
async def export_teachers(db: AsyncSession = Depends(get_db)):
    teachers = await teacher_service.get_all_teachers(db)
    data = [{"ID": t.id, "Логин": t.login, "ФИО": t.name, "Ссылка": t.url or ""} for t in teachers]
    return export_to_excel(data, ["ID", "Логин", "ФИО", "Ссылка"], "Преподаватели", "teachers.xlsx")