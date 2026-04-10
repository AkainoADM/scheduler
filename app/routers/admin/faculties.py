from typing import List
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import faculty as faculty_service
from app.schemas.faculty import FacultyCreate, FacultyUpdate
from app.routers.admin.common import export_to_excel, _common_styles, _import_script, has_dependent_faculty_groups
from app.services.audit import log_action

router = APIRouter(prefix="/admin/faculties", tags=["Admin Faculties"])

def render_faculties_html(faculties):
    html = f"<h1>Факультеты</h1>{_common_styles()}"
    html += "<div><a href='/admin/faculties/export' class='btn-excel'>📎 Экспорт в Excel</a>"
    html += " <button onclick='toggleImportForm_faculties()' class='btn-excel btn-import'>📂 Импорт из Excel</button></div>"
    html += f"<div id='importForm_faculties' class='import-form'>"
    html += f"<form id='uploadForm_faculties' action='/admin/import/faculties' method='post' enctype='multipart/form-data'>"
    html += "<input type='file' name='file' accept='.xlsx,.xls' required>"
    html += "<button type='submit'>Загрузить</button>"
    html += "<button type='button' onclick='toggleImportForm_faculties()'>Отмена</button>"
    html += "</form></div>"
    html += _import_script("faculties")
    html += "<form method='post' action='/admin/faculties/bulk-delete' onsubmit='return confirmDeleteSelected();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllFaculties'> Выделить всё</label>"
    html += "<ul>"
    for f in faculties:
        html += f"<li><input type='checkbox' name='ids' value='{f.id}'> "
        html += f"{f.name} (ID: {f.id})"
        if f.display_name:
            html += f" – {f.display_name}"
        if f.short_display_name:
            html += f" ({f.short_display_name})"
        html += f" <a href='/admin/faculties/edit/{f.id}'>Редактировать</a> "
        html += f"<a href='/admin/faculties/delete/{f.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<form method='post' action='/admin/faculties/add' style='margin-top: 20px;'>"
    html += "<input type='text' name='name' placeholder='Название' required>"
    html += "<input type='text' name='display_name' placeholder='Отображаемое имя'>"
    html += "<input type='text' name='short_display_name' placeholder='Короткое имя'>"
    html += "<button type='submit'>Добавить</button>"
    html += "</form>"
    html += "<a href='/admin/'>На главную админки</a>"
    html += """
    <script>
        const selectAll = document.getElementById('selectAllFaculties');
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
async def faculties_page(db: AsyncSession = Depends(get_db)):
    faculties = await faculty_service.get_all_faculties(db)
    return HTMLResponse(content=render_faculties_html(faculties))

@router.post("/add", response_model=None)
async def add_faculty(
    request: Request,
    name: str = Form(...),
    display_name: str = Form(None),
    short_display_name: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = FacultyCreate(name=name, display_name=display_name, short_display_name=short_display_name)
    faculty = await faculty_service.create_faculty(db, data)
    await log_action(db, "create_faculty", {"id": faculty.id, "name": name, "display_name": display_name, "short_display_name": short_display_name}, request)
    return RedirectResponse(url="/admin/faculties", status_code=303)

@router.get("/edit/{faculty_id}", response_class=HTMLResponse)
async def edit_faculty_form(faculty_id: int, db: AsyncSession = Depends(get_db)):
    faculty = await faculty_service.get_faculty(db, faculty_id)
    if not faculty:
        return HTMLResponse("Факультет не найден", status_code=404)
    html = f"""
    <h1>Редактировать факультет</h1>
    <form method="post" action="/admin/faculties/edit/{faculty_id}">
        <input type="text" name="name" value="{faculty.name}" required>
        <input type="text" name="display_name" value="{faculty.display_name or ''}">
        <input type="text" name="short_display_name" value="{faculty.short_display_name or ''}">
        <button type="submit">Сохранить</button>
    </form>
    <a href="/admin/faculties">Отмена</a>
    """
    return HTMLResponse(content=html)

@router.post("/edit/{faculty_id}", response_model=None)
async def edit_faculty(
    request: Request,
    faculty_id: int,
    name: str = Form(...),
    display_name: str = Form(None),
    short_display_name: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = FacultyUpdate(name=name, display_name=display_name, short_display_name=short_display_name)
    await faculty_service.update_faculty(db, faculty_id, data)
    await log_action(db, "update_faculty", {"id": faculty_id, "name": name, "display_name": display_name, "short_display_name": short_display_name}, request)
    return RedirectResponse(url="/admin/faculties", status_code=303)

@router.get("/delete/{faculty_id}", response_class=HTMLResponse)
async def confirm_delete_faculty(faculty_id: int, db: AsyncSession = Depends(get_db)):
    faculty = await faculty_service.get_faculty(db, faculty_id)
    if not faculty:
        return HTMLResponse("Факультет не найден", status_code=404)
    if await has_dependent_faculty_groups(db, faculty_id):
        html = f"""
        <h1>Ошибка удаления факультета "{faculty.name}"</h1>
        <p>Невозможно удалить факультет, так как к нему привязаны группы. Сначала удалите или переназначьте группы.</p>
        <a href="/admin/faculties">Вернуться к списку факультетов</a>
        """
        return HTMLResponse(content=html, status_code=400)
    html = f"""
    <h1>Удалить факультет "{faculty.name}"?</h1>
    <form method="post" action="/admin/faculties/delete/{faculty_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/faculties">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/delete/{faculty_id}", response_model=None)
async def delete_faculty(
    request: Request,
    faculty_id: int,
    db: AsyncSession = Depends(get_db)
):
    await faculty_service.delete_faculty(db, faculty_id)
    await log_action(db, "delete_faculty", {"id": faculty_id}, request)
    return RedirectResponse(url="/admin/faculties", status_code=303)

@router.post("/bulk-delete", response_model=None)
async def bulk_delete_faculties(
    request: Request,
    ids: List[int] = Form(...),
    db: AsyncSession = Depends(get_db)
):
    await faculty_service.bulk_delete_faculties(db, ids)
    await log_action(db, "bulk_delete_faculties", {"ids": ids}, request)
    return RedirectResponse(url="/admin/faculties", status_code=303)

@router.get("/export")
async def export_faculties(db: AsyncSession = Depends(get_db)):
    faculties = await faculty_service.get_all_faculties(db)
    data = [{"ID": f.id, "Название": f.name, "Отображаемое имя": f.display_name or "", "Короткое имя": f.short_display_name or ""} for f in faculties]
    return export_to_excel(data, ["ID", "Название", "Отображаемое имя", "Короткое имя"], "Факультеты", "faculties.xlsx")