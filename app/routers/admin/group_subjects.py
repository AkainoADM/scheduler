from typing import List
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import group_subject as group_subject_service
from app.services import group as group_service
from app.services import subject as subject_service
from app.routers.admin.common import export_to_excel, _common_styles, _import_script
from app.services.audit import log_action

router = APIRouter(prefix="/admin/group-subjects", tags=["Admin Group Subjects"])

def render_group_subjects_html(group_subjects, groups, subjects):
    html = f"<h1>Связи групп и предметов</h1>{_common_styles()}"
    html += "<div><a href='/admin/group-subjects/export' class='btn-excel'>📎 Экспорт в Excel</a>"
    html += " <button onclick='toggleImportForm_group_subjects()' class='btn-excel btn-import'>📂 Импорт из Excel</button></div>"
    html += f"<div id='importForm_group_subjects' class='import-form'>"
    html += f"<form id='uploadForm_group_subjects' action='/admin/import/group_subjects' method='post' enctype='multipart/form-data'>"
    html += "<input type='file' name='file' accept='.xlsx,.xls' required>"
    html += "<button type='submit'>Загрузить</button>"
    html += "<button type='button' onclick='toggleImportForm_group_subjects()'>Отмена</button>"
    html += "</form></div>"
    html += _import_script("group_subjects")
    html += "<form method='post' action='/admin/group-subjects/add'>"
    html += "<div style='display: flex; gap: 20px; margin-bottom: 10px;'>"
    html += "<div><label>Группы:</label><br>"
    html += "<div style='max-height: 200px; overflow-y: auto; border:1px solid #ccc; padding:8px; width: 250px;'>"
    for g in groups:
        html += f"<label><input type='checkbox' name='group_ids' value='{g.id}'> {g.name}</label><br>"
    html += "</div></div>"
    html += "<div><label>Предметы:</label><br>"
    html += "<div style='max-height: 200px; overflow-y: auto; border:1px solid #ccc; padding:8px; width: 250px;'>"
    for s in subjects:
        html += f"<label><input type='checkbox' name='subject_ids' value='{s.id}'> {s.name}</label><br>"
    html += "</div></div>"
    html += "</div>"
    html += "<button type='submit'>Добавить выбранные комбинации</button>"
    html += "</form>"
    html += "<form method='post' action='/admin/group-subjects/bulk-delete' onsubmit='return confirmDeleteSelectedGS();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllGS'> Выделить всё</label>"
    html += "<ul>"
    for gs in group_subjects:
        html += f"<li><input type='checkbox' name='ids' value='{gs['group_id']},{gs['subject_id']}'> "
        html += f"Группа ID: {gs['group_id']}, Предмет ID: {gs['subject_id']} "
        html += f"<a href='/admin/group-subjects/delete/{gs['group_id']}/{gs['subject_id']}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<a href='/admin/'>На главную админки</a>"
    html += """
    <script>
        const selectAllGS = document.getElementById('selectAllGS');
        if(selectAllGS) selectAllGS.addEventListener('change', function() {
            document.querySelectorAll('input[name="ids"]').forEach(cb => cb.checked = selectAllGS.checked);
        });
        function confirmDeleteSelectedGS() {
            const anyChecked = document.querySelectorAll('input[name="ids"]:checked').length > 0;
            if (!anyChecked) { alert('Не выбрано ни одной записи'); return false; }
            return confirm('Удалить выбранные связи?');
        }
    </script>
    """
    return html

@router.get("", response_class=HTMLResponse)
async def group_subjects_page(db: AsyncSession = Depends(get_db)):
    groups = await group_service.get_all_groups(db)
    subjects = await subject_service.get_all_subjects(db)
    group_subjects = await group_subject_service.get_all_group_subjects(db)
    return HTMLResponse(content=render_group_subjects_html(group_subjects, groups, subjects))

@router.post("/add", response_model=None)
async def add_group_subject(
    request: Request,
    group_ids: List[int] = Form(...),
    subject_ids: List[int] = Form(...),
    db: AsyncSession = Depends(get_db)
):
    added = 0
    for g_id in group_ids:
        for s_id in subject_ids:
            result = await group_subject_service.create_group_subject(db, g_id, s_id)
            if result:
                added += 1
    await log_action(db, "create_group_subject", {"group_ids": group_ids, "subject_ids": subject_ids, "added": added}, request)
    return RedirectResponse(url="/admin/group-subjects", status_code=303)

@router.post("/bulk-delete", response_model=None)
async def bulk_delete_group_subjects(
    request: Request,
    ids: List[str] = Form(...),
    db: AsyncSession = Depends(get_db)
):
    pairs = []
    for item in ids:
        parts = item.split(',')
        if len(parts) == 2:
            pairs.append((int(parts[0]), int(parts[1])))
    await group_subject_service.bulk_delete_group_subjects(db, pairs)
    await log_action(db, "bulk_delete_group_subjects", {"ids": ids}, request)
    return RedirectResponse(url="/admin/group-subjects", status_code=303)

@router.get("/delete/{group_id}/{subject_id}", response_class=HTMLResponse)
async def confirm_delete_group_subject(group_id: int, subject_id: int, db: AsyncSession = Depends(get_db)):
    html = f"""
    <h1>Удалить связь группы {group_id} и предмета {subject_id}?</h1>
    <form method="post" action="/admin/group-subjects/delete/{group_id}/{subject_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/group-subjects">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/delete/{group_id}/{subject_id}", response_model=None)
async def delete_group_subject(
    request: Request,
    group_id: int,
    subject_id: int,
    db: AsyncSession = Depends(get_db)
):
    await group_subject_service.delete_group_subject(db, group_id, subject_id)
    await log_action(db, "delete_group_subject", {"group_id": group_id, "subject_id": subject_id}, request)
    return RedirectResponse(url="/admin/group-subjects", status_code=303)

@router.get("/export")
async def export_group_subjects(db: AsyncSession = Depends(get_db)):
    rels = await group_subject_service.get_all_group_subjects(db)
    groups = await group_service.get_all_groups(db)
    subjects = await subject_service.get_all_subjects(db)
    g_dict = {g.id: g.name for g in groups}
    s_dict = {s.id: s.name for s in subjects}
    data = [{"ID группы": r['group_id'], "Группа": g_dict.get(r['group_id'], ""), "ID предмета": r['subject_id'], "Предмет": s_dict.get(r['subject_id'], "")} for r in rels]
    return export_to_excel(data, ["ID группы", "Группа", "ID предмета", "Предмет"], "Группы-предметы", "group_subjects.xlsx")