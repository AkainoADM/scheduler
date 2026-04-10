from typing import List
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import group as group_service
from app.services import faculty as faculty_service
from app.schemas.group import GroupCreate, GroupUpdate
from app.routers.admin.common import export_to_excel, _common_styles, _import_script
from app.services.audit import log_action

router = APIRouter(prefix="/admin/groups", tags=["Admin Groups"])

def render_groups_html(groups, faculties):
    html = f"<h1>Группы</h1>{_common_styles()}"
    html += "<div><a href='/admin/groups/export' class='btn-excel'>📎 Экспорт в Excel</a>"
    html += " <button onclick='toggleImportForm_groups()' class='btn-excel btn-import'>📂 Импорт из Excel</button></div>"
    html += f"<div id='importForm_groups' class='import-form'>"
    html += f"<form id='uploadForm_groups' action='/admin/import/groups' method='post' enctype='multipart/form-data'>"
    html += "<input type='file' name='file' accept='.xlsx,.xls' required>"
    html += "<button type='submit'>Загрузить</button>"
    html += "<button type='button' onclick='toggleImportForm_groups()'>Отмена</button>"
    html += "</form></div>"
    html += _import_script("groups")
    html += "<form method='post' action='/admin/groups/add'>"
    html += "<input type='text' name='name' placeholder='Название группы' required>"
    html += "<select name='faculty_id' required><option value=''>Выберите факультет</option>"
    for fac in faculties:
        html += f"<option value='{fac.id}'>{fac.name}</option>"
    html += "</select>"
    html += "<input type='number' name='student_count' placeholder='Количество студентов'>"
    html += "<button type='submit'>Добавить</button>"
    html += "</form>"
    html += "<form method='post' action='/admin/groups/bulk-delete' onsubmit='return confirmDeleteSelected();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllGroups'> Выделить всё</label>"
    html += "<ul>"
    for g in groups:
        html += f"<li><input type='checkbox' name='ids' value='{g.id}'> "
        html += f"{g.name} (Факультет ID: {g.faculty_id}, Студентов: {g.student_count}) "
        html += f"<a href='/admin/groups/edit/{g.id}'>Редактировать</a> "
        html += f"<a href='/admin/groups/delete/{g.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<a href='/admin/'>На главную админки</a>"
    html += """
    <script>
        const selectAll = document.getElementById('selectAllGroups');
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

async def has_dependent_groups(db: AsyncSession, faculty_id: int) -> bool:
    from sqlalchemy import select, func
    from app.models.reference import Group
    result = await db.execute(select(func.count()).select_from(Group).where(Group.faculty_id == faculty_id))
    return result.scalar() > 0

@router.get("", response_class=HTMLResponse)
async def groups_page(db: AsyncSession = Depends(get_db)):
    groups = await group_service.get_all_groups(db)
    faculties = await faculty_service.get_all_faculties(db)
    return HTMLResponse(content=render_groups_html(groups, faculties))

@router.post("/add", response_model=None)
async def add_group(
    request: Request,
    name: str = Form(...),
    faculty_id: int = Form(...),
    student_count: int = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = GroupCreate(name=name, faculty_id=faculty_id, student_count=student_count)
    group = await group_service.create_group(db, data)
    await log_action(db, "create_group", {"id": group.id, "name": name, "faculty_id": faculty_id, "student_count": student_count}, request)
    return RedirectResponse(url="/admin/groups", status_code=303)

@router.get("/edit/{group_id}", response_class=HTMLResponse)
async def edit_group_form(group_id: int, db: AsyncSession = Depends(get_db)):
    group = await group_service.get_group(db, group_id)
    if not group:
        return HTMLResponse("Группа не найдена", status_code=404)
    faculties = await faculty_service.get_all_faculties(db)
    html = f"""
    <h1>Редактировать группу</h1>
    <form method="post" action="/admin/groups/edit/{group_id}">
        <input type="text" name="name" value="{group.name}" required>
        <select name="faculty_id">
            {''.join(f'<option value="{f.id}" {"selected" if f.id == group.faculty_id else ""}>{f.name}</option>' for f in faculties)}
        </select>
        <input type="number" name="student_count" value="{group.student_count or ''}">
        <button type="submit">Сохранить</button>
    </form>
    <a href="/admin/groups">Отмена</a>
    """
    return HTMLResponse(content=html)

@router.post("/edit/{group_id}", response_model=None)
async def edit_group(
    request: Request,
    group_id: int,
    name: str = Form(...),
    faculty_id: int = Form(...),
    student_count: int = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = GroupUpdate(name=name, faculty_id=faculty_id, student_count=student_count)
    await group_service.update_group(db, group_id, data)
    await log_action(db, "update_group", {"id": group_id, "name": name, "faculty_id": faculty_id, "student_count": student_count}, request)
    return RedirectResponse(url="/admin/groups", status_code=303)

@router.get("/delete/{group_id}", response_class=HTMLResponse)
async def confirm_delete_group(group_id: int, db: AsyncSession = Depends(get_db)):
    group = await group_service.get_group(db, group_id)
    if not group:
        return HTMLResponse("Группа не найдена", status_code=404)
    # Проверка зависимостей (нужно определить функции has_dependent_group_subjects, has_dependent_group_teachers)
    from app.routers.admin.common import has_dependent_group_subjects, has_dependent_group_teachers
    if await has_dependent_group_subjects(db, group_id) or await has_dependent_group_teachers(db, group_id):
        html = f"""
        <h1>Ошибка удаления группы "{group.name}"</h1>
        <p>Невозможно удалить группу, так как она связана с предметами или преподавателями. Сначала удалите эти связи.</p>
        <a href="/admin/groups">Вернуться к списку групп</a>
        """
        return HTMLResponse(content=html, status_code=400)
    html = f"""
    <h1>Удалить группу "{group.name}"?</h1>
    <form method="post" action="/admin/groups/delete/{group_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/groups">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/delete/{group_id}", response_model=None)
async def delete_group(
    request: Request,
    group_id: int,
    db: AsyncSession = Depends(get_db)
):
    await group_service.delete_group(db, group_id)
    await log_action(db, "delete_group", {"id": group_id}, request)
    return RedirectResponse(url="/admin/groups", status_code=303)

@router.post("/bulk-delete", response_model=None)
async def bulk_delete_groups(
    request: Request,
    ids: List[int] = Form(...),
    db: AsyncSession = Depends(get_db)
):
    # Проверка зависимостей (опущена для краткости)
    await group_service.bulk_delete_groups(db, ids)
    await log_action(db, "bulk_delete_groups", {"ids": ids}, request)
    return RedirectResponse(url="/admin/groups", status_code=303)

@router.get("/export")
async def export_groups(db: AsyncSession = Depends(get_db)):
    groups = await group_service.get_all_groups(db)
    faculties = await faculty_service.get_all_faculties(db)
    fac_dict = {f.id: f.name for f in faculties}
    data = [{"ID": g.id, "Название": g.name, "Факультет ID": g.faculty_id, "Факультет": fac_dict.get(g.faculty_id, ""), "Студентов": g.student_count} for g in groups]
    return export_to_excel(data, ["ID", "Название", "Факультет ID", "Факультет", "Студентов"], "Группы", "groups.xlsx")