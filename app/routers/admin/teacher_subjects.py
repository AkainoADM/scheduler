from typing import List
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.services import teacher_subject as teacher_subject_service
from app.services import teacher as teacher_service
from app.services import subject as subject_service
from app.models.reference import op_teachers_of_pairs
from app.routers.admin.common import export_to_excel, _common_styles, _import_script
from app.services.audit import log_action

router = APIRouter(prefix="/admin/teacher-subjects", tags=["Admin Teacher Subjects"])

def render_teacher_subjects_html(teacher_subjects, teachers, subjects):
    html = f"<h1>Связи преподавателей и предметов</h1>{_common_styles()}"
    html += "<div><a href='/admin/teacher-subjects/export' class='btn-excel'>📎 Экспорт в Excel</a>"
    html += " <button onclick='toggleImportForm_teacher_subjects()' class='btn-excel btn-import'>📂 Импорт из Excel</button></div>"
    html += f"<div id='importForm_teacher_subjects' class='import-form'>"
    html += f"<form id='uploadForm_teacher_subjects' action='/admin/import/teacher_subjects' method='post' enctype='multipart/form-data'>"
    html += "<input type='file' name='file' accept='.xlsx,.xls' required>"
    html += "<button type='submit'>Загрузить</button>"
    html += "<button type='button' onclick='toggleImportForm_teacher_subjects()'>Отмена</button>"
    html += "</form></div>"
    html += _import_script("teacher_subjects")
    html += "<form method='post' action='/admin/teacher-subjects/add'>"
    html += "<div style='display: flex; gap: 20px; margin-bottom: 10px;'>"
    html += "<div><label>Преподаватели:</label><br>"
    html += "<div style='max-height: 200px; overflow-y: auto; border:1px solid #ccc; padding:8px; width: 250px;'>"
    for t in teachers:
        html += f"<label><input type='checkbox' name='teacher_ids' value='{t.id}'> {t.name}</label><br>"
    html += "</div></div>"
    html += "<div><label>Предметы:</label><br>"
    html += "<div style='max-height: 200px; overflow-y: auto; border:1px solid #ccc; padding:8px; width: 250px;'>"
    for s in subjects:
        html += f"<label><input type='checkbox' name='subject_ids' value='{s.id}'> {s.name}</label><br>"
    html += "</div></div>"
    html += "</div>"
    html += "<label><input type='checkbox' name='is_main' value='true'> Основной преподаватель (для всех выбранных комбинаций)</label><br>"
    html += "<button type='submit'>Добавить выбранные комбинации</button>"
    html += "</form>"
    html += "<form method='post' action='/admin/teacher-subjects/bulk-delete' onsubmit='return confirmDeleteSelectedTS();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllTS'> Выделить всё</label>"
    html += "<ul>"
    for ts in teacher_subjects:
        html += f"<li><input type='checkbox' name='ids' value='{ts['teacher_id']},{ts['subject_id']}'> "
        html += f"Преподаватель ID: {ts['teacher_id']}, Предмет ID: {ts['subject_id']}, Основной: {ts['is_main']} "
        html += f"<a href='/admin/teacher-subjects/edit/{ts['teacher_id']}/{ts['subject_id']}'>Редактировать</a> "
        html += f"<a href='/admin/teacher-subjects/delete/{ts['teacher_id']}/{ts['subject_id']}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<a href='/admin/'>На главную админки</a>"
    html += """
    <script>
        const selectAllTS = document.getElementById('selectAllTS');
        if(selectAllTS) selectAllTS.addEventListener('change', function() {
            document.querySelectorAll('input[name="ids"]').forEach(cb => cb.checked = selectAllTS.checked);
        });
        function confirmDeleteSelectedTS() {
            const anyChecked = document.querySelectorAll('input[name="ids"]:checked').length > 0;
            if (!anyChecked) { alert('Не выбрано ни одной записи'); return false; }
            return confirm('Удалить выбранные связи?');
        }
    </script>
    """
    return html

@router.get("", response_class=HTMLResponse)
async def teacher_subjects_page(db: AsyncSession = Depends(get_db)):
    teachers = await teacher_service.get_all_teachers(db)
    subjects = await subject_service.get_all_subjects(db)
    teacher_subjects = await teacher_subject_service.get_all_teacher_subjects(db)
    return HTMLResponse(content=render_teacher_subjects_html(teacher_subjects, teachers, subjects))

@router.post("/add", response_model=None)
async def add_teacher_subject(
    request: Request,
    teacher_ids: List[int] = Form(...),
    subject_ids: List[int] = Form(...),
    is_main: bool = Form(False),
    db: AsyncSession = Depends(get_db)
):
    added = 0
    for t_id in teacher_ids:
        for s_id in subject_ids:
            result = await teacher_subject_service.create_teacher_subject(db, t_id, s_id, is_main)
            if result:
                added += 1
    await log_action(db, "create_teacher_subject", {"teacher_ids": teacher_ids, "subject_ids": subject_ids, "is_main": is_main, "added": added}, request)
    return RedirectResponse(url="/admin/teacher-subjects", status_code=303)

@router.post("/bulk-delete", response_model=None)
async def bulk_delete_teacher_subjects(
    request: Request,
    ids: List[str] = Form(...),
    db: AsyncSession = Depends(get_db)
):
    pairs = []
    for item in ids:
        parts = item.split(',')
        if len(parts) == 2:
            pairs.append((int(parts[0]), int(parts[1])))
    await teacher_subject_service.bulk_delete_teacher_subjects(db, pairs)
    await log_action(db, "bulk_delete_teacher_subjects", {"ids": ids}, request)
    return RedirectResponse(url="/admin/teacher-subjects", status_code=303)

@router.get("/edit/{teacher_id}/{subject_id}", response_class=HTMLResponse)
async def edit_teacher_subject_form(teacher_id: int, subject_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(op_teachers_of_pairs).where(op_teachers_of_pairs.c.teacher_id == teacher_id, op_teachers_of_pairs.c.subject_id == subject_id))
    ts = result.first()
    if not ts:
        return HTMLResponse("Связь не найдена", status_code=404)
    is_main_checked = "checked" if ts.is_main else ""
    html = f"""
    <h1>Редактировать связь преподавателя {teacher_id} и предмета {subject_id}</h1>
    <form method="post" action="/admin/teacher-subjects/edit/{teacher_id}/{subject_id}">
        <label><input type="checkbox" name="is_main" value="true" {is_main_checked}> Основной преподаватель</label>
        <button type="submit">Сохранить</button>
    </form>
    <a href="/admin/teacher-subjects">Отмена</a>
    """
    return HTMLResponse(content=html)

@router.post("/edit/{teacher_id}/{subject_id}", response_model=None)
async def edit_teacher_subject(
    request: Request,
    teacher_id: int,
    subject_id: int,
    is_main: bool = Form(False),
    db: AsyncSession = Depends(get_db)
):
    await teacher_subject_service.update_teacher_subject(db, teacher_id, subject_id, is_main)
    await log_action(db, "update_teacher_subject", {"teacher_id": teacher_id, "subject_id": subject_id, "is_main": is_main}, request)
    return RedirectResponse(url="/admin/teacher-subjects", status_code=303)

@router.get("/delete/{teacher_id}/{subject_id}", response_class=HTMLResponse)
async def confirm_delete_teacher_subject(teacher_id: int, subject_id: int, db: AsyncSession = Depends(get_db)):
    html = f"""
    <h1>Удалить связь преподавателя {teacher_id} и предмета {subject_id}?</h1>
    <form method="post" action="/admin/teacher-subjects/delete/{teacher_id}/{subject_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/teacher-subjects">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/delete/{teacher_id}/{subject_id}", response_model=None)
async def delete_teacher_subject(
    request: Request,
    teacher_id: int,
    subject_id: int,
    db: AsyncSession = Depends(get_db)
):
    await teacher_subject_service.delete_teacher_subject(db, teacher_id, subject_id)
    await log_action(db, "delete_teacher_subject", {"teacher_id": teacher_id, "subject_id": subject_id}, request)
    return RedirectResponse(url="/admin/teacher-subjects", status_code=303)

@router.get("/export")
async def export_teacher_subjects(db: AsyncSession = Depends(get_db)):
    rels = await teacher_subject_service.get_all_teacher_subjects(db)
    teachers = await teacher_service.get_all_teachers(db)
    subjects = await subject_service.get_all_subjects(db)
    t_dict = {t.id: t.name for t in teachers}
    s_dict = {s.id: s.name for s in subjects}
    data = [{"ID учителя": r['teacher_id'], "Учитель": t_dict.get(r['teacher_id'], ""), "ID предмета": r['subject_id'], "Предмет": s_dict.get(r['subject_id'], ""), "Основной": "Да" if r['is_main'] else "Нет"} for r in rels]
    return export_to_excel(data, ["ID учителя", "Учитель", "ID предмета", "Предмет", "Основной"], "Преподаватели-предметы", "teacher_subjects.xlsx")