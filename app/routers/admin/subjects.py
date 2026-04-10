from typing import List
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import subject as subject_service
from app.schemas.subject import SubjectCreate, SubjectUpdate
from app.routers.admin.common import export_to_excel, _common_styles, _import_script, has_dependent_subject_teachers, has_dependent_subject_audiences, has_dependent_subject_groups
from app.services.audit import log_action

router = APIRouter(prefix="/admin/subjects", tags=["Admin Subjects"])

def render_subjects_html(subjects):
    html = f"<h1>Дисциплины</h1>{_common_styles()}"
    html += "<div><a href='/admin/subjects/export' class='btn-excel'>📎 Экспорт в Excel</a>"
    html += " <button onclick='toggleImportForm_subjects()' class='btn-excel btn-import'>📂 Импорт из Excel</button></div>"
    html += f"<div id='importForm_subjects' class='import-form'>"
    html += f"<form id='uploadForm_subjects' action='/admin/import/subjects' method='post' enctype='multipart/form-data'>"
    html += "<input type='file' name='file' accept='.xlsx,.xls' required>"
    html += "<button type='submit'>Загрузить</button>"
    html += "<button type='button' onclick='toggleImportForm_subjects()'>Отмена</button>"
    html += "</form></div>"
    html += _import_script("subjects")
    html += "<form method='post' action='/admin/subjects/bulk-delete' onsubmit='return confirmDeleteSelected();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllSubjects'> Выделить всё</label>"
    html += "<ul>"
    for s in subjects:
        html += f"<li><input type='checkbox' name='ids' value='{s.id}'> "
        html += f"{s.name} "
        html += f"<a href='/admin/subjects/edit/{s.id}'>Редактировать</a> "
        html += f"<a href='/admin/subjects/delete/{s.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<form method='post' action='/admin/subjects/add' style='margin-top: 20px;'>"
    html += "<input type='text' name='name' placeholder='Название дисциплины' required>"
    html += "<button type='submit'>Добавить</button>"
    html += "</form>"
    html += "<a href='/admin/'>На главную админки</a>"
    html += """
    <script>
        const selectAll = document.getElementById('selectAllSubjects');
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
async def subjects_page(db: AsyncSession = Depends(get_db)):
    subjects = await subject_service.get_all_subjects(db)
    return HTMLResponse(content=render_subjects_html(subjects))

@router.post("/add", response_model=None)
async def add_subject(
    request: Request,
    name: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    data = SubjectCreate(name=name)
    subject = await subject_service.create_subject(db, data)
    await log_action(db, "create_subject", {"id": subject.id, "name": name}, request)
    return RedirectResponse(url="/admin/subjects", status_code=303)

@router.get("/edit/{subject_id}", response_class=HTMLResponse)
async def edit_subject_form(subject_id: int, db: AsyncSession = Depends(get_db)):
    subject = await subject_service.get_subject(db, subject_id)
    if not subject:
        return HTMLResponse("Дисциплина не найдена", status_code=404)
    html = f"""
    <h1>Редактировать дисциплину</h1>
    <form method="post" action="/admin/subjects/edit/{subject_id}">
        <input type="text" name="name" value="{subject.name}" required>
        <button type="submit">Сохранить</button>
    </form>
    <a href="/admin/subjects">Отмена</a>
    """
    return HTMLResponse(content=html)

@router.post("/edit/{subject_id}", response_model=None)
async def edit_subject(
    request: Request,
    subject_id: int,
    name: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    data = SubjectUpdate(name=name)
    await subject_service.update_subject(db, subject_id, data)
    await log_action(db, "update_subject", {"id": subject_id, "name": name}, request)
    return RedirectResponse(url="/admin/subjects", status_code=303)

@router.get("/delete/{subject_id}", response_class=HTMLResponse)
async def confirm_delete_subject(subject_id: int, db: AsyncSession = Depends(get_db)):
    subject = await subject_service.get_subject(db, subject_id)
    if not subject:
        return HTMLResponse("Дисциплина не найдена", status_code=404)
    if await has_dependent_subject_teachers(db, subject_id) or await has_dependent_subject_audiences(db, subject_id) or await has_dependent_subject_groups(db, subject_id):
        html = f"""
        <h1>Ошибка удаления дисциплины "{subject.name}"</h1>
        <p>Невозможно удалить дисциплину, так как она связана с преподавателями, аудиториями или группами. Сначала удалите эти связи.</p>
        <a href="/admin/subjects">Вернуться к списку дисциплин</a>
        """
        return HTMLResponse(content=html, status_code=400)
    html = f"""
    <h1>Удалить дисциплину "{subject.name}"?</h1>
    <form method="post" action="/admin/subjects/delete/{subject_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/subjects">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/delete/{subject_id}", response_model=None)
async def delete_subject(
    request: Request,
    subject_id: int,
    db: AsyncSession = Depends(get_db)
):
    await subject_service.delete_subject(db, subject_id)
    await log_action(db, "delete_subject", {"id": subject_id}, request)
    return RedirectResponse(url="/admin/subjects", status_code=303)

@router.post("/bulk-delete", response_model=None)
async def bulk_delete_subjects(
    request: Request,
    ids: List[int] = Form(...),
    db: AsyncSession = Depends(get_db)
):
    await subject_service.bulk_delete_subjects(db, ids)
    await log_action(db, "bulk_delete_subjects", {"ids": ids}, request)
    return RedirectResponse(url="/admin/subjects", status_code=303)

@router.get("/export")
async def export_subjects(db: AsyncSession = Depends(get_db)):
    subjects = await subject_service.get_all_subjects(db)
    data = [{"ID": s.id, "Название": s.name} for s in subjects]
    return export_to_excel(data, ["ID", "Название"], "Дисциплины", "subjects.xlsx")