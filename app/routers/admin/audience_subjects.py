from typing import List
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import audience_subject as audience_subject_service
from app.services import audience as audience_service
from app.services import subject as subject_service
from app.routers.admin.common import export_to_excel, _common_styles, _import_script
from app.services.audit import log_action

router = APIRouter(prefix="/admin/audience-subjects", tags=["Admin Audience Subjects"])

def render_audience_subjects_html(audience_subjects, audiences, subjects):
    html = f"<h1>Связи аудиторий и предметов</h1>{_common_styles()}"
    html += "<div><a href='/admin/audience-subjects/export' class='btn-excel'>📎 Экспорт в Excel</a>"
    html += " <button onclick='toggleImportForm_audience_subjects()' class='btn-excel btn-import'>📂 Импорт из Excel</button></div>"
    html += f"<div id='importForm_audience_subjects' class='import-form'>"
    html += f"<form id='uploadForm_audience_subjects' action='/admin/import/audience_subjects' method='post' enctype='multipart/form-data'>"
    html += "<input type='file' name='file' accept='.xlsx,.xls' required>"
    html += "<button type='submit'>Загрузить</button>"
    html += "<button type='button' onclick='toggleImportForm_audience_subjects()'>Отмена</button>"
    html += "</form></div>"
    html += _import_script("audience_subjects")
    html += "<form method='post' action='/admin/audience-subjects/add'>"
    html += "<div style='display: flex; gap: 20px; margin-bottom: 10px;'>"
    html += "<div><label>Аудитории:</label><br>"
    html += "<div style='max-height: 200px; overflow-y: auto; border:1px solid #ccc; padding:8px; width: 250px;'>"
    for a in audiences:
        html += f"<label><input type='checkbox' name='audience_ids' value='{a.id}'> {a.name}</label><br>"
    html += "</div></div>"
    html += "<div><label>Предметы:</label><br>"
    html += "<div style='max-height: 200px; overflow-y: auto; border:1px solid #ccc; padding:8px; width: 250px;'>"
    for s in subjects:
        html += f"<label><input type='checkbox' name='subject_ids' value='{s.id}'> {s.name}</label><br>"
    html += "</div></div>"
    html += "</div>"
    html += "<button type='submit'>Добавить выбранные комбинации</button>"
    html += "</form>"
    html += "<form method='post' action='/admin/audience-subjects/bulk-delete' onsubmit='return confirmDeleteSelectedAS();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllAS'> Выделить всё</label>"
    html += "<ul>"
    for asub in audience_subjects:
        html += f"<li><input type='checkbox' name='ids' value='{asub['audience_id']},{asub['subject_id']}'> "
        html += f"Аудитория ID: {asub['audience_id']}, Предмет ID: {asub['subject_id']} "
        html += f"<a href='/admin/audience-subjects/delete/{asub['audience_id']}/{asub['subject_id']}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<a href='/admin/'>На главную админки</a>"
    html += """
    <script>
        const selectAllAS = document.getElementById('selectAllAS');
        if(selectAllAS) selectAllAS.addEventListener('change', function() {
            document.querySelectorAll('input[name="ids"]').forEach(cb => cb.checked = selectAllAS.checked);
        });
        function confirmDeleteSelectedAS() {
            const anyChecked = document.querySelectorAll('input[name="ids"]:checked').length > 0;
            if (!anyChecked) { alert('Не выбрано ни одной записи'); return false; }
            return confirm('Удалить выбранные связи?');
        }
    </script>
    """
    return html

@router.get("", response_class=HTMLResponse)
async def audience_subjects_page(db: AsyncSession = Depends(get_db)):
    audiences = await audience_service.get_all_audiences(db)
    subjects = await subject_service.get_all_subjects(db)
    audience_subjects = await audience_subject_service.get_all_audience_subjects(db)
    return HTMLResponse(content=render_audience_subjects_html(audience_subjects, audiences, subjects))

@router.post("/add", response_model=None)
async def add_audience_subject(
    request: Request,
    audience_ids: List[int] = Form(...),
    subject_ids: List[int] = Form(...),
    db: AsyncSession = Depends(get_db)
):
    added = 0
    for a_id in audience_ids:
        for s_id in subject_ids:
            result = await audience_subject_service.create_audience_subject(db, a_id, s_id)
            if result:
                added += 1
    await log_action(db, "create_audience_subject", {"audience_ids": audience_ids, "subject_ids": subject_ids, "added": added}, request)
    return RedirectResponse(url="/admin/audience-subjects", status_code=303)

@router.post("/bulk-delete", response_model=None)
async def bulk_delete_audience_subjects(
    request: Request,
    ids: List[str] = Form(...),
    db: AsyncSession = Depends(get_db)
):
    pairs = []
    for item in ids:
        parts = item.split(',')
        if len(parts) == 2:
            pairs.append((int(parts[0]), int(parts[1])))
    await audience_subject_service.bulk_delete_audience_subjects(db, pairs)
    await log_action(db, "bulk_delete_audience_subjects", {"ids": ids}, request)
    return RedirectResponse(url="/admin/audience-subjects", status_code=303)

@router.get("/delete/{audience_id}/{subject_id}", response_class=HTMLResponse)
async def confirm_delete_audience_subject(audience_id: int, subject_id: int, db: AsyncSession = Depends(get_db)):
    html = f"""
    <h1>Удалить связь аудитории {audience_id} и предмета {subject_id}?</h1>
    <form method="post" action="/admin/audience-subjects/delete/{audience_id}/{subject_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/audience-subjects">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/delete/{audience_id}/{subject_id}", response_model=None)
async def delete_audience_subject(
    request: Request,
    audience_id: int,
    subject_id: int,
    db: AsyncSession = Depends(get_db)
):
    await audience_subject_service.delete_audience_subject(db, audience_id, subject_id)
    await log_action(db, "delete_audience_subject", {"audience_id": audience_id, "subject_id": subject_id}, request)
    return RedirectResponse(url="/admin/audience-subjects", status_code=303)

@router.get("/export")
async def export_audience_subjects(db: AsyncSession = Depends(get_db)):
    rels = await audience_subject_service.get_all_audience_subjects(db)
    audiences = await audience_service.get_all_audiences(db)
    subjects = await subject_service.get_all_subjects(db)
    a_dict = {a.id: a.name for a in audiences}
    s_dict = {s.id: s.name for s in subjects}
    data = [{"ID аудитории": r['audience_id'], "Аудитория": a_dict.get(r['audience_id'], ""), "ID предмета": r['subject_id'], "Предмет": s_dict.get(r['subject_id'], "")} for r in rels]
    return export_to_excel(data, ["ID аудитории", "Аудитория", "ID предмета", "Предмет"], "Аудитории-предметы", "audience_subjects.xlsx")