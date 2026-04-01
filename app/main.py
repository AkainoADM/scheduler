import os
from datetime import date
from typing import List
from fastapi import FastAPI, Depends, Form, Request, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.api.v1 import router as v1_router
from app.core.database import get_db
from app.services import group as group_service
from app.services import teacher as teacher_service
from app.services import audience as audience_service
from app.services import faculty as faculty_service
from app.services import building as building_service
from app.services import calendar as calendar_service
from app.services import calendar_sync
from app.schemas.group import GroupCreate, GroupUpdate
from app.schemas.teacher import TeacherCreate, TeacherUpdate
from app.schemas.audience import AudienceCreate, AudienceUpdate
from app.schemas.building import BuildingCreate, BuildingUpdate
from app.schemas.calendar import CalendarCreate, CalendarUpdate

from app.schemas.faculty import FacultyCreate, FacultyUpdate

from app.schemas.user_type import UserTypeCreate, UserTypeUpdate
from app.schemas.subdivision import SubdivisionCreate, SubdivisionUpdate
from app.schemas.role import RoleCreate, RoleUpdate
from app.schemas.permission import PermissionCreate, PermissionUpdate
from app.schemas.time_slot import TimeSlotCreate, TimeSlotUpdate

from app.services import user_type as user_type_service
from app.services import subdivision as subdivision_service
from app.services import role as role_service
from app.services import permission as permission_service
from app.services import time_slot as time_slot_service

app = FastAPI(title="Schedule Generation System")
app.include_router(v1_router)

# ---------- Вспомогательные функции для рендеринга ----------
def render_groups_html(groups, faculties):
    html = "<h1>Группы</h1>"
    # Форма добавления
    html += "<form method='post' action='/groups/add'>"
    html += "<input type='text' name='name' placeholder='Название группы' required>"
    html += "<select name='faculty_id' required><option value=''>Выберите факультет</option>"
    for fac in faculties:
        html += f"<option value='{fac.id}'>{fac.name}</option>"
    html += "</select>"
    html += "<input type='number' name='student_count' placeholder='Количество студентов'>"
    html += "<button type='submit'>Добавить</button>"
    html += "</form>"
    # Форма массового удаления
    html += "<form method='post' action='/groups/bulk-delete' onsubmit='return confirmDeleteSelected();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllGroups'> Выделить всё</label>"
    html += "<ul>"
    for g in groups:
        html += f"<li><input type='checkbox' name='ids' value='{g.id}'> "
        html += f"{g.name} (Факультет ID: {g.faculty_id}, Студентов: {g.student_count}) "
        html += f"<a href='/groups/edit/{g.id}'>Редактировать</a> "
        html += f"<a href='/groups/delete/{g.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<a href='/'>На главную</a>"
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
            if (!anyChecked) {
                alert('Не выбрано ни одной записи');
                return false;
            }
            return confirm('Вы уверены, что хотите удалить выбранные записи?');
        }
    </script>
    """
    return html

def render_teachers_html(teachers):
    html = "<h1>Преподаватели</h1>"
    html += "<form method='post' action='/teachers/add'>"
    html += "<input type='text' name='login' placeholder='Логин' required>"
    html += "<input type='text' name='name' placeholder='ФИО' required>"
    html += "<input type='text' name='url' placeholder='Ссылка на страницу'>"
    html += "<input type='number' name='max_hours_per_day' placeholder='Макс. часов в день'>"
    html += "<input type='number' name='max_hours_per_week' placeholder='Макс. часов в неделю'>"
    html += "<button type='submit'>Добавить</button>"
    html += "</form>"
    html += "<form method='post' action='/teachers/bulk-delete' onsubmit='return confirmDeleteSelected();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllTeachers'> Выделить всё</label>"
    html += "<ul>"
    for t in teachers:
        html += f"<li><input type='checkbox' name='ids' value='{t.id}'> "
        html += f"{t.name} (Логин: {t.login}, День: {t.max_hours_per_day or 'нет'}, Неделя: {t.max_hours_per_week or 'нет'}) "
        html += f"<a href='/teachers/edit/{t.id}'>Редактировать</a> "
        html += f"<a href='/teachers/delete/{t.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<a href='/'>На главную</a>"
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
            if (!anyChecked) {
                alert('Не выбрано ни одной записи');
                return false;
            }
            return confirm('Вы уверены, что хотите удалить выбранные записи?');
        }
    </script>
    """
    return html

def render_audiences_html(audiences, buildings):
    html = "<h1>Аудитории</h1>"
    html += "<form method='post' action='/audiences/add'>"
    html += "<input type='text' name='name' placeholder='Номер/название' required>"
    html += "<select name='building_id'><option value=''>Не выбрано</option>"
    for b in buildings:
        html += f"<option value='{b.id}'>{b.name}</option>"
    html += "</select>"
    html += "<input type='number' name='capacity' placeholder='Вместимость'>"
    html += "<select name='type'><option value=''>Тип</option><option value='лекционная'>Лекционная</option><option value='практическая'>Практическая</option><option value='лабораторная'>Лабораторная</option><option value='компьютерный класс'>Компьютерный класс</option></select>"
    html += "<label><input type='checkbox' name='is_active' value='true' checked> Активна</label>"
    html += "<button type='submit'>Добавить</button>"
    html += "</form>"
    html += "<form method='post' action='/audiences/bulk-delete' onsubmit='return confirmDeleteSelected();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllAudiences'> Выделить всё</label>"
    html += "<ul>"
    for a in audiences:
        html += f"<li><input type='checkbox' name='ids' value='{a.id}'> "
        html += f"{a.name} (Корпус ID: {a.building_id or 'не указан'}, Мест: {a.capacity or 'не указано'}, Тип: {a.type or 'не указан'}, Активна: {a.is_active}) "
        html += f"<a href='/audiences/edit/{a.id}'>Редактировать</a> "
        html += f"<a href='/audiences/delete/{a.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<a href='/'>На главную</a>"
    html += """
    <script>
        const selectAll = document.getElementById('selectAllAudiences');
        if (selectAll) {
            selectAll.addEventListener('change', function() {
                const checkboxes = document.querySelectorAll('input[name="ids"]');
                checkboxes.forEach(cb => cb.checked = selectAll.checked);
            });
        }
    </script>
    """
    return html

def render_buildings_html(buildings):
    html = "<h1>Здания</h1>"
    html += "<form method='post' action='/buildings/add'>"
    html += "<input type='text' name='name' placeholder='Название здания' required>"
    html += "<input type='text' name='address' placeholder='Адрес'>"
    html += "<button type='submit'>Добавить</button>"
    html += "</form>"
    html += "<form method='post' action='/buildings/bulk-delete' onsubmit='return confirmDeleteSelected();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllBuildings'> Выделить всё</label>"
    html += "<ul>"
    for b in buildings:
        html += f"<li><input type='checkbox' name='ids' value='{b.id}'> "
        html += f"{b.name} (Адрес: {b.address or 'не указан'}) "
        html += f"<a href='/buildings/edit/{b.id}'>Редактировать</a> "
        html += f"<a href='/buildings/delete/{b.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<a href='/'>На главную</a>"
    html += """
    <script>
        const selectAll = document.getElementById('selectAllBuildings');
        if (selectAll) {
            selectAll.addEventListener('change', function() {
                const checkboxes = document.querySelectorAll('input[name="ids"]');
                checkboxes.forEach(cb => cb.checked = selectAll.checked);
            });
        }
    </script>
    """
    return html

def render_calendar_html(entries):
    html = "<h1>Календарь (учебные дни, праздники)</h1>"
    html += "<h2>Добавить запись</h2>"
    html += "<form method='post' action='/calendar/add'>"
    html += "<input type='date' name='date' required>"
    html += "<select name='is_working_day'><option value='true'>Рабочий день</option><option value='false'>Выходной/праздник</option></select>"
    html += "<input type='text' name='description' placeholder='Описание'>"
    html += "<button type='submit'>Добавить</button>"
    html += "</form>"

    html += "<h2>Синхронизация с официальным календарем</h2>"
    html += "<form method='post' action='/calendar/sync'>"
    html += "<input type='number' name='year' placeholder='Год (например, 2025)' required>"
    html += "<button type='submit'>Загрузить данные за год</button>"
    html += "</form>"

    html += "<h2>Список записей</h2>"
    html += "<form method='post' action='/calendar/bulk-delete' onsubmit='return confirmDeleteSelected();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllCalendar'> Выделить всё</label>"
    html += "<ul>"
    for e in entries:
        html += f"<li><input type='checkbox' name='ids' value='{e.id}'> "
        html += f"{e.date} – {'Рабочий' if e.is_working_day else 'Выходной'} "
        if e.description:
            html += f"— {e.description} "
        html += f"<a href='/calendar/edit/{e.id}'>Редактировать</a> "
        html += f"<a href='/calendar/delete/{e.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<a href='/'>На главную</a>"
    html += """
    <script>
        const selectAll = document.getElementById('selectAllCalendar');
        if (selectAll) {
            selectAll.addEventListener('change', function() {
                const checkboxes = document.querySelectorAll('input[name="ids"]');
                checkboxes.forEach(cb => cb.checked = selectAll.checked);
            });
        }
    </script>
    """
    return html

def render_faculties_html(faculties):
    html = "<h1>Факультеты</h1>"
    html += "<form method='post' action='/faculties/bulk-delete' onsubmit='return confirmDeleteSelected();'>"
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
        html += f" <a href='/faculties/edit/{f.id}'>Редактировать</a> "
        html += f"<a href='/faculties/delete/{f.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<form method='post' action='/faculties/add' style='margin-top: 20px;'>"
    html += "<input type='text' name='name' placeholder='Название' required>"
    html += "<input type='text' name='display_name' placeholder='Отображаемое имя'>"
    html += "<input type='text' name='short_display_name' placeholder='Короткое имя'>"
    html += "<button type='submit'>Добавить</button>"
    html += "</form>"
    html += "<a href='/'>На главную</a>"
    html += """
    <script>
        const selectAll = document.getElementById('selectAllFaculties');
        if (selectAll) {
            selectAll.addEventListener('change', function() {
                const checkboxes = document.querySelectorAll('input[name="ids"]');
                checkboxes.forEach(cb => cb.checked = selectAll.checked);
            });
        }
    </script>
    """
    return html

def render_user_types_html(user_types):
    html = "<h1>Типы пользователей</h1>"
    html += "<form method='post' action='/user-types/bulk-delete' onsubmit='return confirmDeleteSelected();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllUserTypes'> Выделить всё</label>"
    html += "<ul>"
    for ut in user_types:
        html += f"<li><input type='checkbox' name='ids' value='{ut.id}'> "
        html += f"{ut.name} (код: {ut.code})"
        if ut.description:
            html += f" – {ut.description}"
        html += f" <a href='/user-types/edit/{ut.id}'>Редактировать</a> "
        html += f"<a href='/user-types/delete/{ut.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<form method='post' action='/user-types/add' style='margin-top: 20px;'>"
    html += "<input type='text' name='code' placeholder='Код (например, teacher)' required>"
    html += "<input type='text' name='name' placeholder='Название' required>"
    html += "<input type='text' name='description' placeholder='Описание'>"
    html += "<button type='submit'>Добавить</button>"
    html += "</form>"
    html += "<a href='/'>На главную</a>"
    html += """
    <script>
        const selectAll = document.getElementById('selectAllUserTypes');
        if (selectAll) {
            selectAll.addEventListener('change', function() {
                const checkboxes = document.querySelectorAll('input[name="ids"]');
                checkboxes.forEach(cb => cb.checked = selectAll.checked);
            });
        }
    </script>
    """
    return html

def render_subdivisions_html(subdivisions):
    html = "<h1>Подразделения</h1>"
    html += "<form method='post' action='/subdivisions/bulk-delete' onsubmit='return confirmDeleteSelected();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllSubdivisions'> Выделить всё</label>"
    html += "<ul>"
    for s in subdivisions:
        html += f"<li><input type='checkbox' name='ids' value='{s.id}'> "
        html += f"{s.name}"
        html += f" <a href='/subdivisions/edit/{s.id}'>Редактировать</a> "
        html += f"<a href='/subdivisions/delete/{s.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<form method='post' action='/subdivisions/add' style='margin-top: 20px;'>"
    html += "<input type='text' name='name' placeholder='Название' required>"
    html += "<button type='submit'>Добавить</button>"
    html += "</form>"
    html += "<a href='/'>На главную</a>"
    html += """
    <script>
        const selectAll = document.getElementById('selectAllSubdivisions');
        if (selectAll) {
            selectAll.addEventListener('change', function() {
                const checkboxes = document.querySelectorAll('input[name="ids"]');
                checkboxes.forEach(cb => cb.checked = selectAll.checked);
            });
        }
    </script>
    """
    return html

def render_roles_html(roles):
    html = "<h1>Роли</h1>"
    html += "<form method='post' action='/roles/bulk-delete' onsubmit='return confirmDeleteSelected();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllRoles'> Выделить всё</label>"
    html += "<ul>"
    for r in roles:
        html += f"<li><input type='checkbox' name='ids' value='{r.id}'> "
        html += f"{r.role_name}"
        if r.description:
            html += f" – {r.description}"
        html += f" <a href='/roles/edit/{r.id}'>Редактировать</a> "
        html += f"<a href='/roles/delete/{r.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<form method='post' action='/roles/add' style='margin-top: 20px;'>"
    html += "<input type='text' name='role_name' placeholder='Название роли' required>"
    html += "<input type='text' name='description' placeholder='Описание'>"
    html += "<button type='submit'>Добавить</button>"
    html += "</form>"
    html += "<a href='/'>На главную</a>"
    html += """
    <script>
        const selectAll = document.getElementById('selectAllRoles');
        if (selectAll) {
            selectAll.addEventListener('change', function() {
                const checkboxes = document.querySelectorAll('input[name="ids"]');
                checkboxes.forEach(cb => cb.checked = selectAll.checked);
            });
        }
    </script>
    """
    return html

def render_permissions_html(permissions):
    html = "<h1>Права</h1>"
    html += "<form method='post' action='/permissions/bulk-delete' onsubmit='return confirmDeleteSelected();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllPermissions'> Выделить всё</label>"
    html += "<ul>"
    for p in permissions:
        html += f"<li><input type='checkbox' name='ids' value='{p.id}'> "
        html += f"{p.permission_name} (код: {p.permission_code})"
        if p.description:
            html += f" – {p.description}"
        html += f" <a href='/permissions/edit/{p.id}'>Редактировать</a> "
        html += f"<a href='/permissions/delete/{p.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<form method='post' action='/permissions/add' style='margin-top: 20px;'>"
    html += "<input type='text' name='permission_code' placeholder='Код права' required>"
    html += "<input type='text' name='permission_name' placeholder='Название' required>"
    html += "<input type='text' name='description' placeholder='Описание'>"
    html += "<button type='submit'>Добавить</button>"
    html += "</form>"
    html += "<a href='/'>На главную</a>"
    html += """
    <script>
        const selectAll = document.getElementById('selectAllPermissions');
        if (selectAll) {
            selectAll.addEventListener('change', function() {
                const checkboxes = document.querySelectorAll('input[name="ids"]');
                checkboxes.forEach(cb => cb.checked = selectAll.checked);
            });
        }
    </script>
    """
    return html

def render_time_slots_html(time_slots):
    html = "<h1>Временные слоты (пары)</h1>"
    html += "<form method='post' action='/time-slots/bulk-delete' onsubmit='return confirmDeleteSelected();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllTimeSlots'> Выделить всё</label>"
    html += "<ul>"
    for ts in time_slots:
        html += f"<li><input type='checkbox' name='ids' value='{ts.id}'> "
        html += f"{ts.name} (№{ts.slot_number}, {ts.start_time}–{ts.end_time})"
        if ts.duration_minutes:
            html += f", длительность: {ts.duration_minutes} мин"
        if not ts.is_active:
            html += " [неактивен]"
        html += f" <a href='/time-slots/edit/{ts.id}'>Редактировать</a> "
        html += f"<a href='/time-slots/delete/{ts.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<form method='post' action='/time-slots/add' style='margin-top: 20px;'>"
    html += "<input type='number' name='slot_number' placeholder='Номер пары' required>"
    html += "<input type='text' name='name' placeholder='Название (например, 1 пара)' required>"
    html += "<input type='time' name='start_time' placeholder='Время начала (HH:MM)' required>"
    html += "<input type='time' name='end_time' placeholder='Время окончания (HH:MM)' required>"
    html += "<input type='number' name='duration_minutes' placeholder='Длительность (мин)'>"
    html += "<input type='number' name='break_after_minutes' placeholder='Перерыв после (мин)'>"
    html += "<label><input type='checkbox' name='is_active' value='true' checked> Активен</label>"
    html += "<button type='submit'>Добавить</button>"
    html += "</form>"
    html += "<a href='/'>На главную</a>"
    html += """
    <script>
        const selectAll = document.getElementById('selectAllTimeSlots');
        if (selectAll) {
            selectAll.addEventListener('change', function() {
                const checkboxes = document.querySelectorAll('input[name="ids"]');
                checkboxes.forEach(cb => cb.checked = selectAll.checked);
            });
        }
    </script>
    """
    return html

# ---------- Страницы ----------
@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse(content="""
    <h1>Система генерации расписания</h1>
    <ul>
        <li><a href='/groups'>Группы</a></li>
        <li><a href='/teachers'>Преподаватели</a></li>
        <li><a href='/audiences'>Аудитории</a></li>
        <li><a href='/buildings'>Здания</a></li>
        <li><a href='/calendar'>Календарь</a></li>
        <li><a href='/faculties'>Факультеты</a></li>
        <li><a href='/user-types'>Типы пользователей</a></li>
        <li><a href='/subdivisions'>Подразделения</a></li>
        <li><a href='/roles'>Роли</a></li>
        <li><a href='/permissions'>Права</a></li>
        <li><a href='/time-slots'>Временные слоты</a></li>
        <li><a href='/docs'>Swagger API</a></li>
        <li><a href='/generate-schedule'>Сгенерировать расписание</a></li>
        <li><a href='/get-schedule'>Получить расписание (JSON)</a></li>
        <li><a href='/dispatcher-proxy'>Просмотр расписания (диспетчер)</a></li>
        <li><a href='http://localhost:8001/docs'>Swagger генератора</a></li>
    </ul>
    """)

# ----- Группы -----
@app.get("/groups", response_class=HTMLResponse)
async def groups_page(db: AsyncSession = Depends(get_db)):
    groups = await group_service.get_all_groups(db)
    faculties = await faculty_service.get_all_faculties(db)
    return HTMLResponse(content=render_groups_html(groups, faculties))

@app.post("/groups/add", response_model=None)
async def add_group(
    name: str = Form(...),
    faculty_id: int = Form(...),
    student_count: int = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = GroupCreate(name=name, faculty_id=faculty_id, student_count=student_count)
    await group_service.create_group(db, data)
    return RedirectResponse(url="/groups", status_code=303)

@app.get("/groups/edit/{group_id}", response_class=HTMLResponse)
async def edit_group_form(group_id: int, db: AsyncSession = Depends(get_db)):
    group = await group_service.get_group(db, group_id)
    if not group:
        return HTMLResponse("Группа не найдена", status_code=404)
    faculties = await faculty_service.get_all_faculties(db)
    html = f"""
    <h1>Редактировать группу</h1>
    <form method="post" action="/groups/edit/{group_id}">
        <input type="text" name="name" value="{group.name}" required>
        <select name="faculty_id">
            {''.join(f'<option value="{f.id}" {"selected" if f.id == group.faculty_id else ""}>{f.name}</option>' for f in faculties)}
        </select>
        <input type="number" name="student_count" value="{group.student_count or ''}">
        <button type="submit">Сохранить</button>
    </form>
    <a href="/groups">Отмена</a>
    """
    return HTMLResponse(content=html)

@app.post("/groups/edit/{group_id}", response_model=None)
async def edit_group(
    group_id: int,
    name: str = Form(...),
    faculty_id: int = Form(...),
    student_count: int = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = GroupUpdate(name=name, faculty_id=faculty_id, student_count=student_count)
    await group_service.update_group(db, group_id, data)
    return RedirectResponse(url="/groups", status_code=303)

@app.get("/groups/delete/{group_id}", response_class=HTMLResponse)
async def confirm_delete_group(group_id: int, db: AsyncSession = Depends(get_db)):
    group = await group_service.get_group(db, group_id)
    if not group:
        return HTMLResponse("Группа не найдена", status_code=404)
    html = f"""
    <h1>Удалить группу "{group.name}"?</h1>
    <form method="post" action="/groups/delete/{group_id}">
        <button type="submit">Да, удалить</button>
        <a href="/groups">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@app.post("/groups/delete/{group_id}", response_model=None)
async def delete_group(group_id: int, db: AsyncSession = Depends(get_db)):
    await group_service.delete_group(db, group_id)
    return RedirectResponse(url="/groups", status_code=303)

@app.post("/groups/bulk-delete", response_model=None)
async def bulk_delete_groups(ids: List[int] = Form(...), db: AsyncSession = Depends(get_db)):
    await group_service.bulk_delete_groups(db, ids)
    return RedirectResponse(url="/groups", status_code=303)

# ----- Преподаватели -----
@app.get("/teachers", response_class=HTMLResponse)
async def teachers_page(db: AsyncSession = Depends(get_db)):
    teachers = await teacher_service.get_all_teachers(db)
    return HTMLResponse(content=render_teachers_html(teachers))

@app.post("/teachers/add", response_model=None)
async def add_teacher(
    login: str = Form(...),
    name: str = Form(...),
    url: str = Form(None),
    max_hours_per_day: int = Form(None),
    max_hours_per_week: int = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = TeacherCreate(login=login, name=name, url=url, max_hours_per_day=max_hours_per_day, max_hours_per_week=max_hours_per_week)
    await teacher_service.create_teacher(db, data)
    return RedirectResponse(url="/teachers", status_code=303)

@app.get("/teachers/edit/{teacher_id}", response_class=HTMLResponse)
async def edit_teacher_form(teacher_id: int, db: AsyncSession = Depends(get_db)):
    teacher = await teacher_service.get_teacher(db, teacher_id)
    if not teacher:
        return HTMLResponse("Преподаватель не найден", status_code=404)
    html = f"""
    <h1>Редактировать преподавателя</h1>
    <form method="post" action="/teachers/edit/{teacher_id}">
        <input type="text" name="login" value="{teacher.login}" required>
        <input type="text" name="name" value="{teacher.name}" required>
        <input type="text" name="url" value="{teacher.url or ''}">
        <input type="number" name="max_hours_per_day" value="{teacher.max_hours_per_day or ''}">
        <input type="number" name="max_hours_per_week" value="{teacher.max_hours_per_week or ''}">
        <button type="submit">Сохранить</button>
    </form>
    <a href="/teachers">Отмена</a>
    """
    return HTMLResponse(content=html)

@app.post("/teachers/edit/{teacher_id}", response_model=None)
async def edit_teacher(
    teacher_id: int,
    login: str = Form(...),
    name: str = Form(...),
    url: str = Form(None),
    max_hours_per_day: int = Form(None),
    max_hours_per_week: int = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = TeacherUpdate(login=login, name=name, url=url, max_hours_per_day=max_hours_per_day, max_hours_per_week=max_hours_per_week)
    await teacher_service.update_teacher(db, teacher_id, data)
    return RedirectResponse(url="/teachers", status_code=303)

@app.get("/teachers/delete/{teacher_id}", response_class=HTMLResponse)
async def confirm_delete_teacher(teacher_id: int, db: AsyncSession = Depends(get_db)):
    teacher = await teacher_service.get_teacher(db, teacher_id)
    if not teacher:
        return HTMLResponse("Преподаватель не найден", status_code=404)
    html = f"""
    <h1>Удалить преподавателя "{teacher.name}"?</h1>
    <form method="post" action="/teachers/delete/{teacher_id}">
        <button type="submit">Да, удалить</button>
        <a href="/teachers">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@app.post("/teachers/delete/{teacher_id}", response_model=None)
async def delete_teacher(teacher_id: int, db: AsyncSession = Depends(get_db)):
    await teacher_service.delete_teacher(db, teacher_id)
    return RedirectResponse(url="/teachers", status_code=303)

@app.post("/teachers/bulk-delete", response_model=None)
async def bulk_delete_teachers(ids: List[int] = Form(...), db: AsyncSession = Depends(get_db)):
    await teacher_service.bulk_delete_teachers(db, ids)
    return RedirectResponse(url="/teachers", status_code=303)

# ----- Аудитории -----
@app.get("/audiences", response_class=HTMLResponse)
async def audiences_page(db: AsyncSession = Depends(get_db)):
    audiences = await audience_service.get_all_audiences(db)
    buildings = await building_service.get_all_buildings(db)
    return HTMLResponse(content=render_audiences_html(audiences, buildings))

@app.post("/audiences/add", response_model=None)
async def add_audience(
    name: str = Form(...),
    building_id: int = Form(None),
    capacity: int = Form(None),
    type: str = Form(None),
    is_active: bool = Form(True),
    db: AsyncSession = Depends(get_db)
):
    data = AudienceCreate(name=name, building_id=building_id, capacity=capacity, type=type, is_active=is_active)
    await audience_service.create_audience(db, data)
    return RedirectResponse(url="/audiences", status_code=303)

@app.get("/audiences/edit/{audience_id}", response_class=HTMLResponse)
async def edit_audience_form(audience_id: int, db: AsyncSession = Depends(get_db)):
    audience = await audience_service.get_audience(db, audience_id)
    if not audience:
        return HTMLResponse("Аудитория не найдена", status_code=404)
    buildings = await building_service.get_all_buildings(db)
    html = f"""
    <h1>Редактировать аудиторию</h1>
    <form method="post" action="/audiences/edit/{audience_id}">
        <input type="text" name="name" value="{audience.name}" required>
        <select name="building_id">
            <option value="">Не выбрано</option>
            {''.join(f'<option value="{b.id}" {"selected" if b.id == audience.building_id else ""}>{b.name}</option>' for b in buildings)}
        </select>
        <input type="number" name="capacity" value="{audience.capacity or ''}">
        <select name="type">
            <option value="">Тип</option>
            <option value="лекционная" {'selected' if audience.type == 'лекционная' else ''}>Лекционная</option>
            <option value="практическая" {'selected' if audience.type == 'практическая' else ''}>Практическая</option>
            <option value="лабораторная" {'selected' if audience.type == 'лабораторная' else ''}>Лабораторная</option>
            <option value="компьютерный класс" {'selected' if audience.type == 'компьютерный класс' else ''}>Компьютерный класс</option>
        </select>
        <label><input type="checkbox" name="is_active" value="true" {'checked' if audience.is_active else ''}> Активна</label>
        <button type="submit">Сохранить</button>
    </form>
    <a href="/audiences">Отмена</a>
    """
    return HTMLResponse(content=html)

@app.post("/audiences/edit/{audience_id}", response_model=None)
async def edit_audience(
    audience_id: int,
    name: str = Form(...),
    building_id: int = Form(None),
    capacity: int = Form(None),
    type: str = Form(None),
    is_active: bool = Form(True),
    db: AsyncSession = Depends(get_db)
):
    data = AudienceUpdate(name=name, building_id=building_id, capacity=capacity, type=type, is_active=is_active)
    await audience_service.update_audience(db, audience_id, data)
    return RedirectResponse(url="/audiences", status_code=303)

@app.get("/audiences/delete/{audience_id}", response_class=HTMLResponse)
async def confirm_delete_audience(audience_id: int, db: AsyncSession = Depends(get_db)):
    audience = await audience_service.get_audience(db, audience_id)
    if not audience:
        return HTMLResponse("Аудитория не найдена", status_code=404)
    html = f"""
    <h1>Удалить аудиторию "{audience.name}"?</h1>
    <form method="post" action="/audiences/delete/{audience_id}">
        <button type="submit">Да, удалить</button>
        <a href="/audiences">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@app.post("/audiences/delete/{audience_id}", response_model=None)
async def delete_audience(audience_id: int, db: AsyncSession = Depends(get_db)):
    await audience_service.delete_audience(db, audience_id)
    return RedirectResponse(url="/audiences", status_code=303)

@app.post("/audiences/bulk-delete", response_model=None)
async def bulk_delete_audiences(ids: List[int] = Form(...), db: AsyncSession = Depends(get_db)):
    await audience_service.bulk_delete_audiences(db, ids)
    return RedirectResponse(url="/audiences", status_code=303)

# ----- Здания -----
@app.get("/buildings", response_class=HTMLResponse)
async def buildings_page(db: AsyncSession = Depends(get_db)):
    buildings = await building_service.get_all_buildings(db)
    return HTMLResponse(content=render_buildings_html(buildings))

@app.post("/buildings/add", response_model=None)
async def add_building(
    name: str = Form(...),
    address: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = BuildingCreate(name=name, address=address)
    await building_service.create_building(db, data)
    return RedirectResponse(url="/buildings", status_code=303)

@app.get("/buildings/edit/{building_id}", response_class=HTMLResponse)
async def edit_building_form(building_id: int, db: AsyncSession = Depends(get_db)):
    building = await building_service.get_building(db, building_id)
    if not building:
        return HTMLResponse("Здание не найдено", status_code=404)
    html = f"""
    <h1>Редактировать здание</h1>
    <form method="post" action="/buildings/edit/{building_id}">
        <input type="text" name="name" value="{building.name}" required>
        <input type="text" name="address" value="{building.address or ''}">
        <button type="submit">Сохранить</button>
    </form>
    <a href="/buildings">Отмена</a>
    """
    return HTMLResponse(content=html)

@app.post("/buildings/edit/{building_id}", response_model=None)
async def edit_building(
    building_id: int,
    name: str = Form(...),
    address: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = BuildingUpdate(name=name, address=address)
    await building_service.update_building(db, building_id, data)
    return RedirectResponse(url="/buildings", status_code=303)

@app.get("/buildings/delete/{building_id}", response_class=HTMLResponse)
async def confirm_delete_building(building_id: int, db: AsyncSession = Depends(get_db)):
    building = await building_service.get_building(db, building_id)
    if not building:
        return HTMLResponse("Здание не найдено", status_code=404)
    html = f"""
    <h1>Удалить здание "{building.name}"?</h1>
    <form method="post" action="/buildings/delete/{building_id}">
        <button type="submit">Да, удалить</button>
        <a href="/buildings">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@app.post("/buildings/delete/{building_id}", response_model=None)
async def delete_building(building_id: int, db: AsyncSession = Depends(get_db)):
    await building_service.delete_building(db, building_id)
    return RedirectResponse(url="/buildings", status_code=303)

@app.post("/buildings/bulk-delete", response_model=None)
async def bulk_delete_buildings(ids: List[int] = Form(...), db: AsyncSession = Depends(get_db)):
    await building_service.bulk_delete_buildings(db, ids)
    return RedirectResponse(url="/buildings", status_code=303)

# ----- Календарь -----
@app.get("/calendar", response_class=HTMLResponse)
async def calendar_page(db: AsyncSession = Depends(get_db)):
    entries = await calendar_service.get_all_calendar(db)
    return HTMLResponse(content=render_calendar_html(entries))

@app.post("/calendar/add", response_model=None)
async def add_calendar_entry(
    date: date = Form(...),
    is_working_day: bool = Form(True),
    description: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = CalendarCreate(date=date, is_working_day=is_working_day, description=description)
    await calendar_service.create_calendar_entry(db, data)
    return RedirectResponse(url="/calendar", status_code=303)

@app.post("/calendar/sync", response_model=None)
async def sync_calendar_web(
    year: int = Form(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    background_tasks.add_task(calendar_sync.sync_calendar_for_year, year)
    return RedirectResponse(url="/calendar", status_code=303)

@app.get("/calendar/edit/{entry_id}", response_class=HTMLResponse)
async def edit_calendar_form(entry_id: int, db: AsyncSession = Depends(get_db)):
    entry = await calendar_service.get_calendar_entry(db, entry_id)
    if not entry:
        return HTMLResponse("Запись не найдена", status_code=404)
    html = f"""
    <h1>Редактировать запись календаря</h1>
    <form method="post" action="/calendar/edit/{entry_id}">
        <input type="date" name="date" value="{entry.date}" required>
        <select name="is_working_day">
            <option value="true" {'selected' if entry.is_working_day else ''}>Рабочий день</option>
            <option value="false" {'selected' if not entry.is_working_day else ''}>Выходной/праздник</option>
        </select>
        <input type="text" name="description" value="{entry.description or ''}">
        <button type="submit">Сохранить</button>
    </form>
    <a href="/calendar">Отмена</a>
    """
    return HTMLResponse(content=html)

@app.post("/calendar/edit/{entry_id}", response_model=None)
async def edit_calendar_entry(
    entry_id: int,
    date: date = Form(...),
    is_working_day: bool = Form(True),
    description: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = CalendarUpdate(date=date, is_working_day=is_working_day, description=description)
    await calendar_service.update_calendar_entry(db, entry_id, data)
    return RedirectResponse(url="/calendar", status_code=303)

@app.get("/calendar/delete/{entry_id}", response_class=HTMLResponse)
async def confirm_delete_calendar(entry_id: int, db: AsyncSession = Depends(get_db)):
    entry = await calendar_service.get_calendar_entry(db, entry_id)
    if not entry:
        return HTMLResponse("Запись не найдена", status_code=404)
    html = f"""
    <h1>Удалить запись за {entry.date}?</h1>
    <form method="post" action="/calendar/delete/{entry_id}">
        <button type="submit">Да, удалить</button>
        <a href="/calendar">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@app.post("/calendar/delete/{entry_id}", response_model=None)
async def delete_calendar_entry(entry_id: int, db: AsyncSession = Depends(get_db)):
    await calendar_service.delete_calendar_entry(db, entry_id)
    return RedirectResponse(url="/calendar", status_code=303)

@app.post("/calendar/bulk-delete", response_model=None)
async def bulk_delete_calendar(ids: List[int] = Form(...), db: AsyncSession = Depends(get_db)):
    await calendar_service.bulk_delete_calendar(db, ids)
    return RedirectResponse(url="/calendar", status_code=303)

# ----- Факультеты -----
@app.get("/faculties", response_class=HTMLResponse)
async def faculties_page(db: AsyncSession = Depends(get_db)):
    faculties = await faculty_service.get_all_faculties(db)
    return HTMLResponse(content=render_faculties_html(faculties))

@app.post("/faculties/add", response_model=None)
async def add_faculty(
    name: str = Form(...),
    display_name: str = Form(None),
    short_display_name: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = FacultyCreate(name=name, display_name=display_name, short_display_name=short_display_name)
    await faculty_service.create_faculty(db, data)
    return RedirectResponse(url="/faculties", status_code=303)

@app.get("/faculties/edit/{faculty_id}", response_class=HTMLResponse)
async def edit_faculty_form(faculty_id: int, db: AsyncSession = Depends(get_db)):
    faculty = await faculty_service.get_faculty(db, faculty_id)
    if not faculty:
        return HTMLResponse("Факультет не найден", status_code=404)
    html = f"""
    <h1>Редактировать факультет</h1>
    <form method="post" action="/faculties/edit/{faculty_id}">
        <input type="text" name="name" value="{faculty.name}" required>
        <input type="text" name="display_name" value="{faculty.display_name or ''}">
        <input type="text" name="short_display_name" value="{faculty.short_display_name or ''}">
        <button type="submit">Сохранить</button>
    </form>
    <a href="/faculties">Отмена</a>
    """
    return HTMLResponse(content=html)

@app.post("/faculties/edit/{faculty_id}", response_model=None)
async def edit_faculty(
    faculty_id: int,
    name: str = Form(...),
    display_name: str = Form(None),
    short_display_name: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = FacultyUpdate(name=name, display_name=display_name, short_display_name=short_display_name)
    await faculty_service.update_faculty(db, faculty_id, data)
    return RedirectResponse(url="/faculties", status_code=303)

@app.get("/faculties/delete/{faculty_id}", response_class=HTMLResponse)
async def confirm_delete_faculty(faculty_id: int, db: AsyncSession = Depends(get_db)):
    faculty = await faculty_service.get_faculty(db, faculty_id)
    if not faculty:
        return HTMLResponse("Факультет не найден", status_code=404)
    html = f"""
    <h1>Удалить факультет "{faculty.name}"?</h1>
    <form method="post" action="/faculties/delete/{faculty_id}">
        <button type="submit">Да, удалить</button>
        <a href="/faculties">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@app.post("/faculties/delete/{faculty_id}", response_model=None)
async def delete_faculty(faculty_id: int, db: AsyncSession = Depends(get_db)):
    await faculty_service.delete_faculty(db, faculty_id)
    return RedirectResponse(url="/faculties", status_code=303)

@app.post("/faculties/bulk-delete", response_model=None)
async def bulk_delete_faculties(ids: List[int] = Form(...), db: AsyncSession = Depends(get_db)):
    await faculty_service.bulk_delete_faculties(db, ids)
    return RedirectResponse(url="/faculties", status_code=303)

# ----- Типы пользователей -----
@app.get("/user-types", response_class=HTMLResponse)
async def user_types_page(db: AsyncSession = Depends(get_db)):
    user_types = await user_type_service.get_all_user_types(db)
    return HTMLResponse(content=render_user_types_html(user_types))

@app.post("/user-types/add", response_model=None)
async def add_user_type(
    code: str = Form(...),
    name: str = Form(...),
    description: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = UserTypeCreate(code=code, name=name, description=description)
    await user_type_service.create_user_type(db, data)
    return RedirectResponse(url="/user-types", status_code=303)

@app.get("/user-types/edit/{ut_id}", response_class=HTMLResponse)
async def edit_user_type_form(ut_id: int, db: AsyncSession = Depends(get_db)):
    ut = await user_type_service.get_user_type(db, ut_id)
    if not ut:
        return HTMLResponse("Тип пользователя не найден", status_code=404)
    html = f"""
    <h1>Редактировать тип пользователя</h1>
    <form method="post" action="/user-types/edit/{ut_id}">
        <input type="text" name="code" value="{ut.code}" required>
        <input type="text" name="name" value="{ut.name}" required>
        <input type="text" name="description" value="{ut.description or ''}">
        <button type="submit">Сохранить</button>
    </form>
    <a href="/user-types">Отмена</a>
    """
    return HTMLResponse(content=html)

@app.post("/user-types/edit/{ut_id}", response_model=None)
async def edit_user_type(
    ut_id: int,
    code: str = Form(...),
    name: str = Form(...),
    description: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = UserTypeUpdate(code=code, name=name, description=description)
    await user_type_service.update_user_type(db, ut_id, data)
    return RedirectResponse(url="/user-types", status_code=303)

@app.get("/user-types/delete/{ut_id}", response_class=HTMLResponse)
async def confirm_delete_user_type(ut_id: int, db: AsyncSession = Depends(get_db)):
    ut = await user_type_service.get_user_type(db, ut_id)
    if not ut:
        return HTMLResponse("Тип пользователя не найден", status_code=404)
    html = f"""
    <h1>Удалить тип "{ut.name}"?</h1>
    <form method="post" action="/user-types/delete/{ut_id}">
        <button type="submit">Да, удалить</button>
        <a href="/user-types">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@app.post("/user-types/delete/{ut_id}", response_model=None)
async def delete_user_type(ut_id: int, db: AsyncSession = Depends(get_db)):
    await user_type_service.delete_user_type(db, ut_id)
    return RedirectResponse(url="/user-types", status_code=303)

@app.post("/user-types/bulk-delete", response_model=None)
async def bulk_delete_user_types(ids: List[int] = Form(...), db: AsyncSession = Depends(get_db)):
    await user_type_service.bulk_delete_user_types(db, ids)
    return RedirectResponse(url="/user-types", status_code=303)

# ----- Подразделения -----
@app.get("/subdivisions", response_class=HTMLResponse)
async def subdivisions_page(db: AsyncSession = Depends(get_db)):
    subdivisions = await subdivision_service.get_all_subdivisions(db)
    return HTMLResponse(content=render_subdivisions_html(subdivisions))

@app.post("/subdivisions/add", response_model=None)
async def add_subdivision(
    name: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    data = SubdivisionCreate(name=name)
    await subdivision_service.create_subdivision(db, data)
    return RedirectResponse(url="/subdivisions", status_code=303)

@app.get("/subdivisions/edit/{sub_id}", response_class=HTMLResponse)
async def edit_subdivision_form(sub_id: int, db: AsyncSession = Depends(get_db)):
    sub = await subdivision_service.get_subdivision(db, sub_id)
    if not sub:
        return HTMLResponse("Подразделение не найдено", status_code=404)
    html = f"""
    <h1>Редактировать подразделение</h1>
    <form method="post" action="/subdivisions/edit/{sub_id}">
        <input type="text" name="name" value="{sub.name}" required>
        <button type="submit">Сохранить</button>
    </form>
    <a href="/subdivisions">Отмена</a>
    """
    return HTMLResponse(content=html)

@app.post("/subdivisions/edit/{sub_id}", response_model=None)
async def edit_subdivision(
    sub_id: int,
    name: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    data = SubdivisionUpdate(name=name)
    await subdivision_service.update_subdivision(db, sub_id, data)
    return RedirectResponse(url="/subdivisions", status_code=303)

@app.get("/subdivisions/delete/{sub_id}", response_class=HTMLResponse)
async def confirm_delete_subdivision(sub_id: int, db: AsyncSession = Depends(get_db)):
    sub = await subdivision_service.get_subdivision(db, sub_id)
    if not sub:
        return HTMLResponse("Подразделение не найдено", status_code=404)
    html = f"""
    <h1>Удалить подразделение "{sub.name}"?</h1>
    <form method="post" action="/subdivisions/delete/{sub_id}">
        <button type="submit">Да, удалить</button>
        <a href="/subdivisions">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@app.post("/subdivisions/delete/{sub_id}", response_model=None)
async def delete_subdivision(sub_id: int, db: AsyncSession = Depends(get_db)):
    await subdivision_service.delete_subdivision(db, sub_id)
    return RedirectResponse(url="/subdivisions", status_code=303)

@app.post("/subdivisions/bulk-delete", response_model=None)
async def bulk_delete_subdivisions(ids: List[int] = Form(...), db: AsyncSession = Depends(get_db)):
    await subdivision_service.bulk_delete_subdivisions(db, ids)
    return RedirectResponse(url="/subdivisions", status_code=303)

# ----- Роли -----
@app.get("/roles", response_class=HTMLResponse)
async def roles_page(db: AsyncSession = Depends(get_db)):
    roles = await role_service.get_all_roles(db)
    return HTMLResponse(content=render_roles_html(roles))

@app.post("/roles/add", response_model=None)
async def add_role(
    role_name: str = Form(...),
    description: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = RoleCreate(role_name=role_name, description=description)
    await role_service.create_role(db, data)
    return RedirectResponse(url="/roles", status_code=303)

@app.get("/roles/edit/{role_id}", response_class=HTMLResponse)
async def edit_role_form(role_id: int, db: AsyncSession = Depends(get_db)):
    role = await role_service.get_role(db, role_id)
    if not role:
        return HTMLResponse("Роль не найдена", status_code=404)
    html = f"""
    <h1>Редактировать роль</h1>
    <form method="post" action="/roles/edit/{role_id}">
        <input type="text" name="role_name" value="{role.role_name}" required>
        <input type="text" name="description" value="{role.description or ''}">
        <button type="submit">Сохранить</button>
    </form>
    <a href="/roles">Отмена</a>
    """
    return HTMLResponse(content=html)

@app.post("/roles/edit/{role_id}", response_model=None)
async def edit_role(
    role_id: int,
    role_name: str = Form(...),
    description: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = RoleUpdate(role_name=role_name, description=description)
    await role_service.update_role(db, role_id, data)
    return RedirectResponse(url="/roles", status_code=303)

@app.get("/roles/delete/{role_id}", response_class=HTMLResponse)
async def confirm_delete_role(role_id: int, db: AsyncSession = Depends(get_db)):
    role = await role_service.get_role(db, role_id)
    if not role:
        return HTMLResponse("Роль не найдена", status_code=404)
    html = f"""
    <h1>Удалить роль "{role.role_name}"?</h1>
    <form method="post" action="/roles/delete/{role_id}">
        <button type="submit">Да, удалить</button>
        <a href="/roles">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@app.post("/roles/delete/{role_id}", response_model=None)
async def delete_role(role_id: int, db: AsyncSession = Depends(get_db)):
    await role_service.delete_role(db, role_id)
    return RedirectResponse(url="/roles", status_code=303)

@app.post("/roles/bulk-delete", response_model=None)
async def bulk_delete_roles(ids: List[int] = Form(...), db: AsyncSession = Depends(get_db)):
    await role_service.bulk_delete_roles(db, ids)
    return RedirectResponse(url="/roles", status_code=303)

# ----- Права -----
@app.get("/permissions", response_class=HTMLResponse)
async def permissions_page(db: AsyncSession = Depends(get_db)):
    permissions = await permission_service.get_all_permissions(db)
    return HTMLResponse(content=render_permissions_html(permissions))

@app.post("/permissions/add", response_model=None)
async def add_permission(
    permission_code: str = Form(...),
    permission_name: str = Form(...),
    description: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = PermissionCreate(permission_code=permission_code, permission_name=permission_name, description=description)
    await permission_service.create_permission(db, data)
    return RedirectResponse(url="/permissions", status_code=303)

@app.get("/permissions/edit/{perm_id}", response_class=HTMLResponse)
async def edit_permission_form(perm_id: int, db: AsyncSession = Depends(get_db)):
    perm = await permission_service.get_permission(db, perm_id)
    if not perm:
        return HTMLResponse("Право не найдено", status_code=404)
    html = f"""
    <h1>Редактировать право</h1>
    <form method="post" action="/permissions/edit/{perm_id}">
        <input type="text" name="permission_code" value="{perm.permission_code}" required>
        <input type="text" name="permission_name" value="{perm.permission_name}" required>
        <input type="text" name="description" value="{perm.description or ''}">
        <button type="submit">Сохранить</button>
    </form>
    <a href="/permissions">Отмена</a>
    """
    return HTMLResponse(content=html)

@app.post("/permissions/edit/{perm_id}", response_model=None)
async def edit_permission(
    perm_id: int,
    permission_code: str = Form(...),
    permission_name: str = Form(...),
    description: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = PermissionUpdate(permission_code=permission_code, permission_name=permission_name, description=description)
    await permission_service.update_permission(db, perm_id, data)
    return RedirectResponse(url="/permissions", status_code=303)

@app.get("/permissions/delete/{perm_id}", response_class=HTMLResponse)
async def confirm_delete_permission(perm_id: int, db: AsyncSession = Depends(get_db)):
    perm = await permission_service.get_permission(db, perm_id)
    if not perm:
        return HTMLResponse("Право не найдено", status_code=404)
    html = f"""
    <h1>Удалить право "{perm.permission_name}"?</h1>
    <form method="post" action="/permissions/delete/{perm_id}">
        <button type="submit">Да, удалить</button>
        <a href="/permissions">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@app.post("/permissions/delete/{perm_id}", response_model=None)
async def delete_permission(perm_id: int, db: AsyncSession = Depends(get_db)):
    await permission_service.delete_permission(db, perm_id)
    return RedirectResponse(url="/permissions", status_code=303)

@app.post("/permissions/bulk-delete", response_model=None)
async def bulk_delete_permissions(ids: List[int] = Form(...), db: AsyncSession = Depends(get_db)):
    await permission_service.bulk_delete_permissions(db, ids)
    return RedirectResponse(url="/permissions", status_code=303)

# ----- Временные слоты -----
@app.get("/time-slots", response_class=HTMLResponse)
async def time_slots_page(db: AsyncSession = Depends(get_db)):
    time_slots = await time_slot_service.get_all_time_slots(db)
    return HTMLResponse(content=render_time_slots_html(time_slots))

@app.post("/time-slots/add", response_model=None)
async def add_time_slot(
    slot_number: int = Form(...),
    name: str = Form(...),
    start_time: str = Form(...),   # будет парситься в time
    end_time: str = Form(...),
    duration_minutes: int = Form(None),
    break_after_minutes: int = Form(None),
    is_active: bool = Form(True),
    db: AsyncSession = Depends(get_db)
):
    from datetime import time
    start = time.fromisoformat(start_time)
    end = time.fromisoformat(end_time)
    data = TimeSlotCreate(
        slot_number=slot_number,
        name=name,
        start_time=start,
        end_time=end,
        duration_minutes=duration_minutes,
        break_after_minutes=break_after_minutes,
        is_active=is_active
    )
    await time_slot_service.create_time_slot(db, data)
    return RedirectResponse(url="/time-slots", status_code=303)

@app.get("/time-slots/edit/{ts_id}", response_class=HTMLResponse)
async def edit_time_slot_form(ts_id: int, db: AsyncSession = Depends(get_db)):
    ts = await time_slot_service.get_time_slot(db, ts_id)
    if not ts:
        return HTMLResponse("Слот не найден", status_code=404)
    html = f"""
    <h1>Редактировать временной слот</h1>
    <form method="post" action="/time-slots/edit/{ts_id}">
        <input type="number" name="slot_number" value="{ts.slot_number}" required>
        <input type="text" name="name" value="{ts.name}" required>
        <input type="time" name="start_time" value="{ts.start_time.isoformat()}" required>
        <input type="time" name="end_time" value="{ts.end_time.isoformat()}" required>
        <input type="number" name="duration_minutes" value="{ts.duration_minutes or ''}">
        <input type="number" name="break_after_minutes" value="{ts.break_after_minutes or ''}">
        <label><input type="checkbox" name="is_active" value="true" {'checked' if ts.is_active else ''}> Активен</label>
        <button type="submit">Сохранить</button>
    </form>
    <a href="/time-slots">Отмена</a>
    """
    return HTMLResponse(content=html)

@app.post("/time-slots/edit/{ts_id}", response_model=None)
async def edit_time_slot(
    ts_id: int,
    slot_number: int = Form(...),
    name: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    duration_minutes: int = Form(None),
    break_after_minutes: int = Form(None),
    is_active: bool = Form(True),
    db: AsyncSession = Depends(get_db)
):
    from datetime import time
    start = time.fromisoformat(start_time)
    end = time.fromisoformat(end_time)
    data = TimeSlotUpdate(
        slot_number=slot_number,
        name=name,
        start_time=start,
        end_time=end,
        duration_minutes=duration_minutes,
        break_after_minutes=break_after_minutes,
        is_active=is_active
    )
    await time_slot_service.update_time_slot(db, ts_id, data)
    return RedirectResponse(url="/time-slots", status_code=303)

@app.get("/time-slots/delete/{ts_id}", response_class=HTMLResponse)
async def confirm_delete_time_slot(ts_id: int, db: AsyncSession = Depends(get_db)):
    ts = await time_slot_service.get_time_slot(db, ts_id)
    if not ts:
        return HTMLResponse("Слот не найден", status_code=404)
    html = f"""
    <h1>Удалить слот "{ts.name}"?</h1>
    <form method="post" action="/time-slots/delete/{ts_id}">
        <button type="submit">Да, удалить</button>
        <a href="/time-slots">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@app.post("/time-slots/delete/{ts_id}", response_model=None)
async def delete_time_slot(ts_id: int, db: AsyncSession = Depends(get_db)):
    await time_slot_service.delete_time_slot(db, ts_id)
    return RedirectResponse(url="/time-slots", status_code=303)

@app.post("/time-slots/bulk-delete", response_model=None)
async def bulk_delete_time_slots(ids: List[int] = Form(...), db: AsyncSession = Depends(get_db)):
    await time_slot_service.bulk_delete_time_slots(db, ids)
    return RedirectResponse(url="/time-slots", status_code=303)

# ========== Тестовый эндпоинт ==========
@app.get("/db-check")
async def db_check(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT version()"))
    version = result.scalar()
    return {"postgres_version": version}

# ---------- Взаимодействие с сервером генерации ----------
import httpx
from fastapi import HTTPException, Request

@app.get("/generate-schedule")
async def generate_schedule():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post("http://localhost:8001/api/generate", timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError as e:
            raise HTTPException(status_code=503, detail=f"Не удалось подключиться к серверу генерации: {e}")
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Сервер генерации не ответил вовремя")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=500, detail=f"Ошибка генерации: {e.response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Неожиданная ошибка: {e}")

@app.get("/get-schedule")
async def get_schedule():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8001/api/schedule", timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Сервер генерации недоступен: {e}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=500, detail=f"Ошибка получения расписания: {e.response.text}")

@app.get("/dispatcher-proxy")
async def dispatcher_proxy(request: Request):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8001/schedule/dispatcher", timeout=30.0)
            response.raise_for_status()
            return HTMLResponse(content=response.text)
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Сервер генерации недоступен: {e}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=500, detail=f"Ошибка получения страницы: {e.response.text}")

@app.get("/my-schedule", response_class=HTMLResponse)
async def my_schedule(request: Request):
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8001/api/schedule")
        data = response.json()
    html = "<h1>Расписание</h1>"
    if not data:
        html += "<p>Расписание пусто. Сначала сгенерируйте его.</p>"
    else:
        html += "<table border='1'>发现<th>Предмет</th><th>Преподаватель</th><th>Аудитория</th><th>Дата</th><th>Пара</th><th>Время</th>劝"
        for row in data:
            html += f"<tr><td>{row['subject']}</td><td>{row['teacher']}</td><td>{row['audience']}</td><td>{row['date']}</td><td>{row['pair']}</td><td>{row['time']}</td></tr>"
        html += " ame"
    html += "<p><a href='/'>На главную</a></p>"
    return HTMLResponse(content=html)