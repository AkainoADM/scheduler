from typing import List
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import teacher as teacher_service
from app.services import group as group_service
from app.services import teacher_group as teacher_group_service
from app.routers.admin.common import export_to_excel, _common_styles, _import_script
from app.services.audit import log_action

router = APIRouter(prefix="/admin/teacher-groups", tags=["Admin Teacher Groups"])

def render_teacher_groups_html(teacher_groups, teachers, groups):
    html = f"<h1>Связи преподавателей и групп</h1>{_common_styles()}"
    html += "<div><a href='/admin/teacher-groups/export' class='btn-excel'>📎 Экспорт в Excel</a>"
    html += " <button onclick='toggleImportForm_teacher_groups()' class='btn-excel btn-import'>📂 Импорт из Excel</button></div>"
    html += f"<div id='importForm_teacher_groups' class='import-form'>"
    html += f"<form id='uploadForm_teacher_groups' action='/admin/import/teacher_groups' method='post' enctype='multipart/form-data'>"
    html += "<input type='file' name='file' accept='.xlsx,.xls' required>"
    html += "<button type='submit'>Загрузить</button>"
    html += "<button type='button' onclick='toggleImportForm_teacher_groups()'>Отмена</button>"
    html += "</form></div>"
    html += _import_script("teacher_groups")
    html += "<form method='post' action='/admin/teacher-groups/add'>"
    html += "<div style='display: flex; gap: 20px;'>"
    html += "<div><label>Преподаватели:</label><br>"
    html += "<div style='max-height: 200px; overflow-y: auto; border:1px solid #ccc; padding:8px; width: 250px;'>"
    for t in teachers:
        html += f"<label><input type='checkbox' name='teacher_ids' value='{t.id}'> {t.name}</label><br>"
    html += "</div></div>"
    html += "<div><label>Группы:</label><br>"
    html += "<div style='max-height: 200px; overflow-y: auto; border:1px solid #ccc; padding:8px; width: 250px;'>"
    for g in groups:
        html += f"<label><input type='checkbox' name='group_ids' value='{g.id}'> {g.name}</label><br>"
    html += "</div></div>"
    html += "</div>"
    html += "<button type='submit'>Добавить выбранные комбинации</button>"
    html += "</form>"
    html += "<form method='post' action='/admin/teacher-groups/bulk-delete' onsubmit='return confirmDeleteSelectedTG();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllTG'> Выделить всё</label>"
    html += "<ul>"
    for tg in teacher_groups:
        html += f"<li><input type='checkbox' name='ids' value='{tg['teacher_id']},{tg['group_id']}'> "
        html += f"{tg['teacher_id']} – {tg['group_id']} (Преподаватель ID: {tg['teacher_id']}, Группа ID: {tg['group_id']}) "
        html += f"<a href='/admin/teacher-groups/delete/{tg['teacher_id']}/{tg['group_id']}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<a href='/admin/'>На главную админки</a>"
    html += """
    <script>
        const selectAllTG = document.getElementById('selectAllTG');
        if(selectAllTG) selectAllTG.addEventListener('change', function() {
            document.querySelectorAll('input[name="ids"]').forEach(cb => cb.checked = selectAllTG.checked);
        });
        function confirmDeleteSelectedTG() {
            const anyChecked = document.querySelectorAll('input[name="ids"]:checked').length > 0;
            if (!anyChecked) { alert('Не выбрано ни одной записи'); return false; }
            return confirm('Удалить выбранные связи?');
        }
    </script>
    """
    return html

@router.get("", response_class=HTMLResponse)
async def teacher_groups_page(db: AsyncSession = Depends(get_db)):
    teachers = await teacher_service.get_all_teachers(db)
    groups = await group_service.get_all_groups(db)
    teacher_groups = await teacher_group_service.get_all_teacher_groups(db)
    return HTMLResponse(content=render_teacher_groups_html(teacher_groups, teachers, groups))

@router.post("/add", response_model=None)
async def add_teacher_group(
    request: Request,
    teacher_ids: List[int] = Form(...),
    group_ids: List[int] = Form(...),
    db: AsyncSession = Depends(get_db)
):
    added = 0
    for t_id in teacher_ids:
        for g_id in group_ids:
            result = await teacher_group_service.create_teacher_group(db, t_id, g_id)
            if result:
                added += 1
    await log_action(db, "add_teacher_groups", {"teacher_ids": teacher_ids, "group_ids": group_ids, "added": added}, request)
    return RedirectResponse(url="/admin/teacher-groups", status_code=303)

@router.post("/bulk-delete", response_model=None)
async def bulk_delete_teacher_groups(
    request: Request,
    ids: List[str] = Form(...),
    db: AsyncSession = Depends(get_db)
):
    pairs = []
    for item in ids:
        parts = item.split(',')
        if len(parts) == 2:
            pairs.append((int(parts[0]), int(parts[1])))
    await teacher_group_service.bulk_delete_teacher_groups(db, pairs)
    await log_action(db, "bulk_delete_teacher_groups", {"pairs": pairs}, request)
    return RedirectResponse(url="/admin/teacher-groups", status_code=303)

@router.get("/delete/{teacher_id}/{group_id}", response_class=HTMLResponse)
async def confirm_delete_teacher_group(teacher_id: int, group_id: int, db: AsyncSession = Depends(get_db)):
    html = f"""
    <h1>Удалить связь преподавателя {teacher_id} и группы {group_id}?</h1>
    <form method="post" action="/admin/teacher-groups/delete/{teacher_id}/{group_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/teacher-groups">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/delete/{teacher_id}/{group_id}", response_model=None)
async def delete_teacher_group(
    request: Request,
    teacher_id: int,
    group_id: int,
    db: AsyncSession = Depends(get_db)
):
    await teacher_group_service.delete_teacher_group(db, teacher_id, group_id)
    await log_action(db, "delete_teacher_group", {"teacher_id": teacher_id, "group_id": group_id}, request)
    return RedirectResponse(url="/admin/teacher-groups", status_code=303)

@router.get("/export")
async def export_teacher_groups(db: AsyncSession = Depends(get_db)):
    rels = await teacher_group_service.get_all_teacher_groups(db)
    teachers = await teacher_service.get_all_teachers(db)
    groups = await group_service.get_all_groups(db)
    t_dict = {t.id: t.name for t in teachers}
    g_dict = {g.id: g.name for g in groups}
    data = [{"ID учителя": r['teacher_id'], "Учитель": t_dict.get(r['teacher_id'], ""), "ID группы": r['group_id'], "Группа": g_dict.get(r['group_id'], "")} for r in rels]
    return export_to_excel(data, ["ID учителя", "Учитель", "ID группы", "Группа"], "Преподаватели-группы", "teacher_groups.xlsx")