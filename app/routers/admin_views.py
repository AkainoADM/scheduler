import os
from datetime import date
from typing import List
from fastapi import APIRouter, Depends, Form, Request, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.services import (
    group as group_service,
    teacher as teacher_service,
    audience as audience_service,
    faculty as faculty_service,
    building as building_service,
    calendar as calendar_service,
    user_type as user_type_service,
    subdivision as subdivision_service,
    role as role_service,
    permission as permission_service,
    time_slot as time_slot_service,
    subject as subject_service
)
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
from app.schemas.subject import SubjectCreate, SubjectUpdate

from app.services import teacher_group as teacher_group_service
from app.services import teacher_subject as teacher_subject_service
from app.services import audience_subject as audience_subject_service
from app.services import group_subject as group_subject_service
from app.schemas.teacher_group import TeacherGroupCreate
from app.schemas.teacher_subject import TeacherSubjectCreate, TeacherSubjectUpdate
from app.schemas.audience_subject import AudienceSubjectCreate
from app.schemas.group_subject import GroupSubjectCreate

router = APIRouter(prefix="/admin", tags=["Admin Pages"])

# ---------- Вспомогательные функции для рендеринга ----------
def render_groups_html(groups, faculties):
    html = "<h1>Группы</h1>"
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
    html += "<form method='post' action='/admin/audiences/add'>"
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
    html += "<form method='post' action='/admin/audiences/bulk-delete' onsubmit='return confirmDeleteSelected();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllAudiences'> Выделить всё</label>"
    html += "<ul>"
    for a in audiences:
        html += f"<li><input type='checkbox' name='ids' value='{a.id}'> "
        html += f"{a.name} (Корпус ID: {a.building_id or 'не указан'}, Мест: {a.capacity or 'не указано'}, Тип: {a.type or 'не указан'}, Активна: {a.is_active}) "
        html += f"<a href='/admin/audiences/edit/{a.id}'>Редактировать</a> "
        html += f"<a href='/admin/audiences/delete/{a.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<a href='/admin/'>На главную админки</a>"
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
    html += "<form method='post' action='/admin/buildings/add'>"
    html += "<input type='text' name='name' placeholder='Название здания' required>"
    html += "<input type='text' name='address' placeholder='Адрес'>"
    html += "<button type='submit'>Добавить</button>"
    html += "</form>"
    html += "<form method='post' action='/admin/buildings/bulk-delete' onsubmit='return confirmDeleteSelected();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllBuildings'> Выделить всё</label>"
    html += "<ul>"
    for b in buildings:
        html += f"<li><input type='checkbox' name='ids' value='{b.id}'> "
        html += f"{b.name} (Адрес: {b.address or 'не указан'}) "
        html += f"<a href='/admin/buildings/edit/{b.id}'>Редактировать</a> "
        html += f"<a href='/admin/buildings/delete/{b.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<a href='/admin/'>На главную админки</a>"
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
    html += "<form method='post' action='/admin/calendar/add'>"
    html += "<input type='date' name='date' required>"
    html += "<select name='is_working_day'><option value='true'>Рабочий день</option><option value='false'>Выходной/праздник</option></select>"
    html += "<input type='text' name='description' placeholder='Описание'>"
    html += "<button type='submit'>Добавить</button>"
    html += "</form>"

    html += "<h2>Синхронизация с официальным календарем</h2>"
    html += "<form method='post' action='/admin/calendar/sync'>"
    html += "<input type='number' name='year' placeholder='Год (например, 2025)' required>"
    html += "<button type='submit'>Загрузить данные за год</button>"
    html += "</form>"

    html += "<h2>Список записей</h2>"
    html += "<form method='post' action='/admin/calendar/bulk-delete' onsubmit='return confirmDeleteSelected();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllCalendar'> Выделить всё</label>"
    html += "<ul>"
    for e in entries:
        html += f"<li><input type='checkbox' name='ids' value='{e.id}'> "
        html += f"{e.date} – {'Рабочий' if e.is_working_day else 'Выходной'} "
        if e.description:
            html += f"— {e.description} "
        html += f"<a href='/admin/calendar/edit/{e.id}'>Редактировать</a> "
        html += f"<a href='/admin/calendar/delete/{e.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<a href='/admin/'>На главную админки</a>"
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
    </script>
    """
    return html

def render_user_types_html(user_types):
    html = "<h1>Типы пользователей</h1>"
    html += "<form method='post' action='/admin/user-types/bulk-delete' onsubmit='return confirmDeleteSelected();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllUserTypes'> Выделить всё</label>"
    html += "<ul>"
    for ut in user_types:
        html += f"<li><input type='checkbox' name='ids' value='{ut.id}'> "
        html += f"{ut.name} (код: {ut.code})"
        if ut.description:
            html += f" – {ut.description}"
        html += f" <a href='/admin/user-types/edit/{ut.id}'>Редактировать</a> "
        html += f"<a href='/admin/user-types/delete/{ut.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<form method='post' action='/admin/user-types/add' style='margin-top: 20px;'>"
    html += "<input type='text' name='code' placeholder='Код (например, teacher)' required>"
    html += "<input type='text' name='name' placeholder='Название' required>"
    html += "<input type='text' name='description' placeholder='Описание'>"
    html += "<button type='submit'>Добавить</button>"
    html += "</form>"
    html += "<a href='/admin/'>На главную админки</a>"
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
    html += "<form method='post' action='/admin/subdivisions/bulk-delete' onsubmit='return confirmDeleteSelected();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllSubdivisions'> Выделить всё</label>"
    html += "<ul>"
    for s in subdivisions:
        html += f"<li><input type='checkbox' name='ids' value='{s.id}'> "
        html += f"{s.name}"
        html += f" <a href='/admin/subdivisions/edit/{s.id}'>Редактировать</a> "
        html += f"<a href='/admin/subdivisions/delete/{s.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<form method='post' action='/admin/subdivisions/add' style='margin-top: 20px;'>"
    html += "<input type='text' name='name' placeholder='Название' required>"
    html += "<button type='submit'>Добавить</button>"
    html += "</form>"
    html += "<a href='/admin/'>На главную админки</a>"
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
    html += "<form method='post' action='/admin/roles/bulk-delete' onsubmit='return confirmDeleteSelected();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllRoles'> Выделить всё</label>"
    html += "<ul>"
    for r in roles:
        html += f"<li><input type='checkbox' name='ids' value='{r.id}'> "
        html += f"{r.role_name}"
        if r.description:
            html += f" – {r.description}"
        html += f" <a href='/admin/roles/edit/{r.id}'>Редактировать</a> "
        html += f"<a href='/admin/roles/delete/{r.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<form method='post' action='/admin/roles/add' style='margin-top: 20px;'>"
    html += "<input type='text' name='role_name' placeholder='Название роли' required>"
    html += "<input type='text' name='description' placeholder='Описание'>"
    html += "<button type='submit'>Добавить</button>"
    html += "</form>"
    html += "<a href='/admin/'>На главную админки</a>"
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
    html += "<form method='post' action='/admin/permissions/bulk-delete' onsubmit='return confirmDeleteSelected();'>"
    html += "<button type='submit'>Удалить выбранные</button>"
    html += "<label><input type='checkbox' id='selectAllPermissions'> Выделить всё</label>"
    html += "<ul>"
    for p in permissions:
        html += f"<li><input type='checkbox' name='ids' value='{p.id}'> "
        html += f"{p.permission_name} (код: {p.permission_code})"
        if p.description:
            html += f" – {p.description}"
        html += f" <a href='/admin/permissions/edit/{p.id}'>Редактировать</a> "
        html += f"<a href='/admin/permissions/delete/{p.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<form method='post' action='/admin/permissions/add' style='margin-top: 20px;'>"
    html += "<input type='text' name='permission_code' placeholder='Код права' required>"
    html += "<input type='text' name='permission_name' placeholder='Название' required>"
    html += "<input type='text' name='description' placeholder='Описание'>"
    html += "<button type='submit'>Добавить</button>"
    html += "</form>"
    html += "<a href='/admin/'>На главную админки</a>"
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
    html += "<form method='post' action='/admin/time-slots/bulk-delete' onsubmit='return confirmDeleteSelected();'>"
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
        html += f" <a href='/admin/time-slots/edit/{ts.id}'>Редактировать</a> "
        html += f"<a href='/admin/time-slots/delete/{ts.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "</form>"
    html += "<form method='post' action='/admin/time-slots/add' style='margin-top: 20px;'>"
    html += "<input type='number' name='slot_number' placeholder='Номер пары' required>"
    html += "<input type='text' name='name' placeholder='Название (например, 1 пара)' required>"
    html += "<input type='time' name='start_time' placeholder='Время начала (HH:MM)' required>"
    html += "<input type='time' name='end_time' placeholder='Время окончания (HH:MM)' required>"
    html += "<input type='number' name='duration_minutes' placeholder='Длительность (мин)'>"
    html += "<input type='number' name='break_after_minutes' placeholder='Перерыв после (мин)'>"
    html += "<label><input type='checkbox' name='is_active' value='true' checked> Активен</label>"
    html += "<button type='submit'>Добавить</button>"
    html += "</form>"
    html += "<a href='/admin/'>На главную админки</a>"
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

def render_subjects_html(subjects):
    html = "<h1>Дисциплины</h1>"
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
    </script>
    """
    return html

def render_teacher_groups_html(teacher_groups, teachers, groups):
    html = "<h1>Связи преподавателей и групп</h1>"
    html += "<form method='post' action='/admin/teacher-groups/add'>"
    html += "<div style='display: flex; gap: 20px;'>"
    html += "<div><label>Преподаватели (Ctrl+клик для множественного выбора):</label><br>"
    html += "<select name='teacher_ids' multiple size='6' style='min-width: 200px;'>"
    for t in teachers:
        html += f"<option value='{t.id}'>{t.name}</option>"
    html += "</select></div>"
    html += "<div><label>Группы (Ctrl+клик для множественного выбора):</label><br>"
    html += "<select name='group_ids' multiple size='6' style='min-width: 200px;'>"
    for g in groups:
        html += f"<option value='{g.id}'>{g.name}</option>"
    html += "</select></div>"
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

def render_teacher_subjects_html(teacher_subjects, teachers, subjects):
    html = "<h1>Связи преподавателей и предметов</h1>"
    html += "<form method='post' action='/admin/teacher-subjects/add'>"
    html += "<div style='display: flex; gap: 20px; margin-bottom: 20px;'>"
    html += "<div><label>Преподаватели (Ctrl+клик для множественного выбора):</label><br>"
    html += "<select name='teacher_ids' multiple size='6' style='min-width: 200px;'>"
    for t in teachers:
        html += f"<option value='{t.id}'>{t.name}</option>"
    html += "</select></div>"
    html += "<div><label>Предметы (Ctrl+клик для множественного выбора):</label><br>"
    html += "<select name='subject_ids' multiple size='6' style='min-width: 200px;'>"
    for s in subjects:
        html += f"<option value='{s.id}'>{s.name}</option>"
    html += "</select></div>"
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

def render_audience_subjects_html(audience_subjects, audiences, subjects):
    html = "<h1>Связи аудиторий и предметов</h1>"
    html += "<form method='post' action='/admin/audience-subjects/add'>"
    html += "<div style='display: flex; gap: 20px; margin-bottom: 20px;'>"
    html += "<div><label>Аудитории (Ctrl+клик для множественного выбора):</label><br>"
    html += "<select name='audience_ids' multiple size='6' style='min-width: 200px;'>"
    for a in audiences:
        html += f"<option value='{a.id}'>{a.name}</option>"
    html += "</select></div>"
    html += "<div><label>Предметы (Ctrl+клик для множественного выбора):</label><br>"
    html += "<select name='subject_ids' multiple size='6' style='min-width: 200px;'>"
    for s in subjects:
        html += f"<option value='{s.id}'>{s.name}</option>"
    html += "</select></div>"
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

def render_group_subjects_html(group_subjects, groups, subjects):
    html = "<h1>Связи групп и предметов</h1>"
    html += "<form method='post' action='/admin/group-subjects/add'>"
    html += "<div style='display: flex; gap: 20px; margin-bottom: 20px;'>"
    html += "<div><label>Группы (Ctrl+клик для множественного выбора):</label><br>"
    html += "<select name='group_ids' multiple size='6' style='min-width: 200px;'>"
    for g in groups:
        html += f"<option value='{g.id}'>{g.name}</option>"
    html += "</select></div>"
    html += "<div><label>Предметы (Ctrl+клик для множественного выбора):</label><br>"
    html += "<select name='subject_ids' multiple size='6' style='min-width: 200px;'>"
    for s in subjects:
        html += f"<option value='{s.id}'>{s.name}</option>"
    html += "</select></div>"
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

# ---------- Маршруты для админки ----------
@router.get("/", response_class=HTMLResponse)
async def admin_home():
    return HTMLResponse(content="""
    <h1>Административная панель</h1>
    <ul>
        <li><a href='/admin/groups'>Группы</a></li>
        <li><a href='/admin/teachers'>Преподаватели</a></li>
        <li><a href='/admin/audiences'>Аудитории</a></li>
        <li><a href='/admin/buildings'>Здания</a></li>
        <li><a href='/admin/calendar'>Календарь</a></li>
        <li><a href='/admin/faculties'>Факультеты</a></li>
        <li><a href='/admin/user-types'>Типы пользователей</a></li>
        <li><a href='/admin/subdivisions'>Подразделения</a></li>
        <li><a href='/admin/roles'>Роли</a></li>
        <li><a href='/admin/permissions'>Права</a></li>
        <li><a href='/admin/time-slots'>Временные слоты</a></li>
        <li><a href='/admin/subjects'>Дисциплины</a></li>
        <li><a href='/admin/teacher-groups'>Связи: преподаватели-группы</a></li>
        <li><a href='/admin/teacher-subjects'>Связи: преподаватели-предметы</a></li>
        <li><a href='/admin/audience-subjects'>Связи: аудитории-предметы</a></li>
        <li><a href='/admin/group-subjects'>Связи: группы-предметы</a></li>
    </ul>
    <a href='/'>На главную API</a>
    """)

# ----- Группы -----
@router.get("/groups", response_class=HTMLResponse)
async def groups_page(db: AsyncSession = Depends(get_db)):
    groups = await group_service.get_all_groups(db)
    faculties = await faculty_service.get_all_faculties(db)
    return HTMLResponse(content=render_groups_html(groups, faculties))

@router.post("/groups/add", response_model=None)
async def add_group(
    name: str = Form(...),
    faculty_id: int = Form(...),
    student_count: int = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = GroupCreate(name=name, faculty_id=faculty_id, student_count=student_count)
    await group_service.create_group(db, data)
    return RedirectResponse(url="/admin/groups", status_code=303)

@router.get("/groups/edit/{group_id}", response_class=HTMLResponse)
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

@router.post("/groups/edit/{group_id}", response_model=None)
async def edit_group(
    group_id: int,
    name: str = Form(...),
    faculty_id: int = Form(...),
    student_count: int = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = GroupUpdate(name=name, faculty_id=faculty_id, student_count=student_count)
    await group_service.update_group(db, group_id, data)
    return RedirectResponse(url="/admin/groups", status_code=303)

@router.get("/groups/delete/{group_id}", response_class=HTMLResponse)
async def confirm_delete_group(group_id: int, db: AsyncSession = Depends(get_db)):
    group = await group_service.get_group(db, group_id)
    if not group:
        return HTMLResponse("Группа не найдена", status_code=404)
    html = f"""
    <h1>Удалить группу "{group.name}"?</h1>
    <form method="post" action="/admin/groups/delete/{group_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/groups">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/groups/delete/{group_id}", response_model=None)
async def delete_group(group_id: int, db: AsyncSession = Depends(get_db)):
    await group_service.delete_group(db, group_id)
    return RedirectResponse(url="/admin/groups", status_code=303)

@router.post("/groups/bulk-delete", response_model=None)
async def bulk_delete_groups(ids: List[int] = Form(...), db: AsyncSession = Depends(get_db)):
    await group_service.bulk_delete_groups(db, ids)
    return RedirectResponse(url="/admin/groups", status_code=303)

# ----- Преподаватели -----
@router.get("/teachers", response_class=HTMLResponse)
async def teachers_page(db: AsyncSession = Depends(get_db)):
    teachers = await teacher_service.get_all_teachers(db)
    return HTMLResponse(content=render_teachers_html(teachers))

@router.post("/teachers/add", response_model=None)
async def add_teacher(
    login: str = Form(...),
    name: str = Form(...),
    url: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = TeacherCreate(login=login, name=name, url=url)
    await teacher_service.create_teacher(db, data)
    return RedirectResponse(url="/admin/teachers", status_code=303)

@router.get("/teachers/edit/{teacher_id}", response_class=HTMLResponse)
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

@router.post("/teachers/edit/{teacher_id}", response_model=None)
async def edit_teacher(
    teacher_id: int,
    login: str = Form(...),
    name: str = Form(...),
    url: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = TeacherUpdate(login=login, name=name, url=url)
    await teacher_service.update_teacher(db, teacher_id, data)
    return RedirectResponse(url="/admin/teachers", status_code=303)

@router.get("/teachers/delete/{teacher_id}", response_class=HTMLResponse)
async def confirm_delete_teacher(teacher_id: int, db: AsyncSession = Depends(get_db)):
    teacher = await teacher_service.get_teacher(db, teacher_id)
    if not teacher:
        return HTMLResponse("Преподаватель не найден", status_code=404)
    html = f"""
    <h1>Удалить преподавателя "{teacher.name}"?</h1>
    <form method="post" action="/admin/teachers/delete/{teacher_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/teachers">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/teachers/delete/{teacher_id}", response_model=None)
async def delete_teacher(teacher_id: int, db: AsyncSession = Depends(get_db)):
    await teacher_service.delete_teacher(db, teacher_id)
    return RedirectResponse(url="/admin/teachers", status_code=303)

@router.post("/teachers/bulk-delete", response_model=None)
async def bulk_delete_teachers(ids: List[int] = Form(...), db: AsyncSession = Depends(get_db)):
    await teacher_service.bulk_delete_teachers(db, ids)
    return RedirectResponse(url="/admin/teachers", status_code=303)

# ----- Аудитории -----
@router.get("/audiences", response_class=HTMLResponse)
async def audiences_page(db: AsyncSession = Depends(get_db)):
    audiences = await audience_service.get_all_audiences(db)
    buildings = await building_service.get_all_buildings(db)
    return HTMLResponse(content=render_audiences_html(audiences, buildings))

@router.post("/audiences/add", response_model=None)
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
    return RedirectResponse(url="/admin/audiences", status_code=303)

@router.get("/audiences/edit/{audience_id}", response_class=HTMLResponse)
async def edit_audience_form(audience_id: int, db: AsyncSession = Depends(get_db)):
    audience = await audience_service.get_audience(db, audience_id)
    if not audience:
        return HTMLResponse("Аудитория не найдена", status_code=404)
    buildings = await building_service.get_all_buildings(db)
    html = f"""
    <h1>Редактировать аудиторию</h1>
    <form method="post" action="/admin/audiences/edit/{audience_id}">
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
    <a href="/admin/audiences">Отмена</a>
    """
    return HTMLResponse(content=html)

@router.post("/audiences/edit/{audience_id}", response_model=None)
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
    return RedirectResponse(url="/admin/audiences", status_code=303)

@router.get("/audiences/delete/{audience_id}", response_class=HTMLResponse)
async def confirm_delete_audience(audience_id: int, db: AsyncSession = Depends(get_db)):
    audience = await audience_service.get_audience(db, audience_id)
    if not audience:
        return HTMLResponse("Аудитория не найдена", status_code=404)
    html = f"""
    <h1>Удалить аудиторию "{audience.name}"?</h1>
    <form method="post" action="/admin/audiences/delete/{audience_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/audiences">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/audiences/delete/{audience_id}", response_model=None)
async def delete_audience(audience_id: int, db: AsyncSession = Depends(get_db)):
    await audience_service.delete_audience(db, audience_id)
    return RedirectResponse(url="/admin/audiences", status_code=303)

@router.post("/audiences/bulk-delete", response_model=None)
async def bulk_delete_audiences(ids: List[int] = Form(...), db: AsyncSession = Depends(get_db)):
    await audience_service.bulk_delete_audiences(db, ids)
    return RedirectResponse(url="/admin/audiences", status_code=303)

# ----- Здания -----
@router.get("/buildings", response_class=HTMLResponse)
async def buildings_page(db: AsyncSession = Depends(get_db)):
    buildings = await building_service.get_all_buildings(db)
    return HTMLResponse(content=render_buildings_html(buildings))

@router.post("/buildings/add", response_model=None)
async def add_building(
    name: str = Form(...),
    address: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = BuildingCreate(name=name, address=address)
    await building_service.create_building(db, data)
    return RedirectResponse(url="/admin/buildings", status_code=303)

@router.get("/buildings/edit/{building_id}", response_class=HTMLResponse)
async def edit_building_form(building_id: int, db: AsyncSession = Depends(get_db)):
    building = await building_service.get_building(db, building_id)
    if not building:
        return HTMLResponse("Здание не найдено", status_code=404)
    html = f"""
    <h1>Редактировать здание</h1>
    <form method="post" action="/admin/buildings/edit/{building_id}">
        <input type="text" name="name" value="{building.name}" required>
        <input type="text" name="address" value="{building.address or ''}">
        <button type="submit">Сохранить</button>
    </form>
    <a href="/admin/buildings">Отмена</a>
    """
    return HTMLResponse(content=html)

@router.post("/buildings/edit/{building_id}", response_model=None)
async def edit_building(
    building_id: int,
    name: str = Form(...),
    address: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = BuildingUpdate(name=name, address=address)
    await building_service.update_building(db, building_id, data)
    return RedirectResponse(url="/admin/buildings", status_code=303)

@router.get("/buildings/delete/{building_id}", response_class=HTMLResponse)
async def confirm_delete_building(building_id: int, db: AsyncSession = Depends(get_db)):
    building = await building_service.get_building(db, building_id)
    if not building:
        return HTMLResponse("Здание не найдено", status_code=404)
    html = f"""
    <h1>Удалить здание "{building.name}"?</h1>
    <form method="post" action="/admin/buildings/delete/{building_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/buildings">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/buildings/delete/{building_id}", response_model=None)
async def delete_building(building_id: int, db: AsyncSession = Depends(get_db)):
    await building_service.delete_building(db, building_id)
    return RedirectResponse(url="/admin/buildings", status_code=303)

@router.post("/buildings/bulk-delete", response_model=None)
async def bulk_delete_buildings(ids: List[int] = Form(...), db: AsyncSession = Depends(get_db)):
    await building_service.bulk_delete_buildings(db, ids)
    return RedirectResponse(url="/admin/buildings", status_code=303)

# ----- Календарь -----
@router.get("/calendar", response_class=HTMLResponse)
async def calendar_page(db: AsyncSession = Depends(get_db)):
    entries = await calendar_service.get_all_calendar(db)
    return HTMLResponse(content=render_calendar_html(entries))

@router.post("/calendar/add", response_model=None)
async def add_calendar_entry(
    date: date = Form(...),
    is_working_day: bool = Form(True),
    description: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = CalendarCreate(date=date, is_working_day=is_working_day, description=description)
    await calendar_service.create_calendar_entry(db, data)
    return RedirectResponse(url="/admin/calendar", status_code=303)

@router.post("/calendar/sync", response_model=None)
async def sync_calendar_web(
    year: int = Form(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    background_tasks.add_task(calendar_sync.sync_calendar_for_year, year)
    return RedirectResponse(url="/admin/calendar", status_code=303)

@router.get("/calendar/edit/{entry_id}", response_class=HTMLResponse)
async def edit_calendar_form(entry_id: int, db: AsyncSession = Depends(get_db)):
    entry = await calendar_service.get_calendar_entry(db, entry_id)
    if not entry:
        return HTMLResponse("Запись не найдена", status_code=404)
    html = f"""
    <h1>Редактировать запись календаря</h1>
    <form method="post" action="/admin/calendar/edit/{entry_id}">
        <input type="date" name="date" value="{entry.date}" required>
        <select name="is_working_day">
            <option value="true" {'selected' if entry.is_working_day else ''}>Рабочий день</option>
            <option value="false" {'selected' if not entry.is_working_day else ''}>Выходной/праздник</option>
        </select>
        <input type="text" name="description" value="{entry.description or ''}">
        <button type="submit">Сохранить</button>
    </form>
    <a href="/admin/calendar">Отмена</a>
    """
    return HTMLResponse(content=html)

@router.post("/calendar/edit/{entry_id}", response_model=None)
async def edit_calendar_entry(
    entry_id: int,
    date: date = Form(...),
    is_working_day: bool = Form(True),
    description: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = CalendarUpdate(date=date, is_working_day=is_working_day, description=description)
    await calendar_service.update_calendar_entry(db, entry_id, data)
    return RedirectResponse(url="/admin/calendar", status_code=303)

@router.get("/calendar/delete/{entry_id}", response_class=HTMLResponse)
async def confirm_delete_calendar(entry_id: int, db: AsyncSession = Depends(get_db)):
    entry = await calendar_service.get_calendar_entry(db, entry_id)
    if not entry:
        return HTMLResponse("Запись не найдена", status_code=404)
    html = f"""
    <h1>Удалить запись за {entry.date}?</h1>
    <form method="post" action="/admin/calendar/delete/{entry_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/calendar">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/calendar/delete/{entry_id}", response_model=None)
async def delete_calendar_entry(entry_id: int, db: AsyncSession = Depends(get_db)):
    await calendar_service.delete_calendar_entry(db, entry_id)
    return RedirectResponse(url="/admin/calendar", status_code=303)

@router.post("/calendar/bulk-delete", response_model=None)
async def bulk_delete_calendar(ids: List[int] = Form(...), db: AsyncSession = Depends(get_db)):
    await calendar_service.bulk_delete_calendar(db, ids)
    return RedirectResponse(url="/admin/calendar", status_code=303)

# ----- Факультеты -----
@router.get("/faculties", response_class=HTMLResponse)
async def faculties_page(db: AsyncSession = Depends(get_db)):
    faculties = await faculty_service.get_all_faculties(db)
    return HTMLResponse(content=render_faculties_html(faculties))

@router.post("/faculties/add", response_model=None)
async def add_faculty(
    name: str = Form(...),
    display_name: str = Form(None),
    short_display_name: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = FacultyCreate(name=name, display_name=display_name, short_display_name=short_display_name)
    await faculty_service.create_faculty(db, data)
    return RedirectResponse(url="/admin/faculties", status_code=303)

@router.get("/faculties/edit/{faculty_id}", response_class=HTMLResponse)
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

@router.post("/faculties/edit/{faculty_id}", response_model=None)
async def edit_faculty(
    faculty_id: int,
    name: str = Form(...),
    display_name: str = Form(None),
    short_display_name: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = FacultyUpdate(name=name, display_name=display_name, short_display_name=short_display_name)
    await faculty_service.update_faculty(db, faculty_id, data)
    return RedirectResponse(url="/admin/faculties", status_code=303)

@router.get("/faculties/delete/{faculty_id}", response_class=HTMLResponse)
async def confirm_delete_faculty(faculty_id: int, db: AsyncSession = Depends(get_db)):
    faculty = await faculty_service.get_faculty(db, faculty_id)
    if not faculty:
        return HTMLResponse("Факультет не найден", status_code=404)
    html = f"""
    <h1>Удалить факультет "{faculty.name}"?</h1>
    <form method="post" action="/admin/faculties/delete/{faculty_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/faculties">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/faculties/delete/{faculty_id}", response_model=None)
async def delete_faculty(faculty_id: int, db: AsyncSession = Depends(get_db)):
    await faculty_service.delete_faculty(db, faculty_id)
    return RedirectResponse(url="/admin/faculties", status_code=303)

@router.post("/faculties/bulk-delete", response_model=None)
async def bulk_delete_faculties(ids: List[int] = Form(...), db: AsyncSession = Depends(get_db)):
    await faculty_service.bulk_delete_faculties(db, ids)
    return RedirectResponse(url="/admin/faculties", status_code=303)

# ----- Типы пользователей -----
@router.get("/user-types", response_class=HTMLResponse)
async def user_types_page(db: AsyncSession = Depends(get_db)):
    user_types = await user_type_service.get_all_user_types(db)
    return HTMLResponse(content=render_user_types_html(user_types))

@router.post("/user-types/add", response_model=None)
async def add_user_type(
    code: str = Form(...),
    name: str = Form(...),
    description: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = UserTypeCreate(code=code, name=name, description=description)
    await user_type_service.create_user_type(db, data)
    return RedirectResponse(url="/admin/user-types", status_code=303)

@router.get("/user-types/edit/{ut_id}", response_class=HTMLResponse)
async def edit_user_type_form(ut_id: int, db: AsyncSession = Depends(get_db)):
    ut = await user_type_service.get_user_type(db, ut_id)
    if not ut:
        return HTMLResponse("Тип пользователя не найден", status_code=404)
    html = f"""
    <h1>Редактировать тип пользователя</h1>
    <form method="post" action="/admin/user-types/edit/{ut_id}">
        <input type="text" name="code" value="{ut.code}" required>
        <input type="text" name="name" value="{ut.name}" required>
        <input type="text" name="description" value="{ut.description or ''}">
        <button type="submit">Сохранить</button>
    </form>
    <a href="/admin/user-types">Отмена</a>
    """
    return HTMLResponse(content=html)

@router.post("/user-types/edit/{ut_id}", response_model=None)
async def edit_user_type(
    ut_id: int,
    code: str = Form(...),
    name: str = Form(...),
    description: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = UserTypeUpdate(code=code, name=name, description=description)
    await user_type_service.update_user_type(db, ut_id, data)
    return RedirectResponse(url="/admin/user-types", status_code=303)

@router.get("/user-types/delete/{ut_id}", response_class=HTMLResponse)
async def confirm_delete_user_type(ut_id: int, db: AsyncSession = Depends(get_db)):
    ut = await user_type_service.get_user_type(db, ut_id)
    if not ut:
        return HTMLResponse("Тип пользователя не найден", status_code=404)
    html = f"""
    <h1>Удалить тип "{ut.name}"?</h1>
    <form method="post" action="/admin/user-types/delete/{ut_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/user-types">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/user-types/delete/{ut_id}", response_model=None)
async def delete_user_type(ut_id: int, db: AsyncSession = Depends(get_db)):
    await user_type_service.delete_user_type(db, ut_id)
    return RedirectResponse(url="/admin/user-types", status_code=303)

@router.post("/user-types/bulk-delete", response_model=None)
async def bulk_delete_user_types(ids: List[int] = Form(...), db: AsyncSession = Depends(get_db)):
    await user_type_service.bulk_delete_user_types(db, ids)
    return RedirectResponse(url="/admin/user-types", status_code=303)

# ----- Подразделения -----
@router.get("/subdivisions", response_class=HTMLResponse)
async def subdivisions_page(db: AsyncSession = Depends(get_db)):
    subdivisions = await subdivision_service.get_all_subdivisions(db)
    return HTMLResponse(content=render_subdivisions_html(subdivisions))

@router.post("/subdivisions/add", response_model=None)
async def add_subdivision(
    name: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    data = SubdivisionCreate(name=name)
    await subdivision_service.create_subdivision(db, data)
    return RedirectResponse(url="/admin/subdivisions", status_code=303)

@router.get("/subdivisions/edit/{sub_id}", response_class=HTMLResponse)
async def edit_subdivision_form(sub_id: int, db: AsyncSession = Depends(get_db)):
    sub = await subdivision_service.get_subdivision(db, sub_id)
    if not sub:
        return HTMLResponse("Подразделение не найдено", status_code=404)
    html = f"""
    <h1>Редактировать подразделение</h1>
    <form method="post" action="/admin/subdivisions/edit/{sub_id}">
        <input type="text" name="name" value="{sub.name}" required>
        <button type="submit">Сохранить</button>
    </form>
    <a href="/admin/subdivisions">Отмена</a>
    """
    return HTMLResponse(content=html)

@router.post("/subdivisions/edit/{sub_id}", response_model=None)
async def edit_subdivision(
    sub_id: int,
    name: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    data = SubdivisionUpdate(name=name)
    await subdivision_service.update_subdivision(db, sub_id, data)
    return RedirectResponse(url="/admin/subdivisions", status_code=303)

@router.get("/subdivisions/delete/{sub_id}", response_class=HTMLResponse)
async def confirm_delete_subdivision(sub_id: int, db: AsyncSession = Depends(get_db)):
    sub = await subdivision_service.get_subdivision(db, sub_id)
    if not sub:
        return HTMLResponse("Подразделение не найдено", status_code=404)
    html = f"""
    <h1>Удалить подразделение "{sub.name}"?</h1>
    <form method="post" action="/admin/subdivisions/delete/{sub_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/subdivisions">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/subdivisions/delete/{sub_id}", response_model=None)
async def delete_subdivision(sub_id: int, db: AsyncSession = Depends(get_db)):
    await subdivision_service.delete_subdivision(db, sub_id)
    return RedirectResponse(url="/admin/subdivisions", status_code=303)

@router.post("/subdivisions/bulk-delete", response_model=None)
async def bulk_delete_subdivisions(ids: List[int] = Form(...), db: AsyncSession = Depends(get_db)):
    await subdivision_service.bulk_delete_subdivisions(db, ids)
    return RedirectResponse(url="/admin/subdivisions", status_code=303)

# ----- Роли -----
@router.get("/roles", response_class=HTMLResponse)
async def roles_page(db: AsyncSession = Depends(get_db)):
    roles = await role_service.get_all_roles(db)
    return HTMLResponse(content=render_roles_html(roles))

@router.post("/roles/add", response_model=None)
async def add_role(
    role_name: str = Form(...),
    description: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = RoleCreate(role_name=role_name, description=description)
    await role_service.create_role(db, data)
    return RedirectResponse(url="/admin/roles", status_code=303)

@router.get("/roles/edit/{role_id}", response_class=HTMLResponse)
async def edit_role_form(role_id: int, db: AsyncSession = Depends(get_db)):
    role = await role_service.get_role(db, role_id)
    if not role:
        return HTMLResponse("Роль не найдена", status_code=404)
    html = f"""
    <h1>Редактировать роль</h1>
    <form method="post" action="/admin/roles/edit/{role_id}">
        <input type="text" name="role_name" value="{role.role_name}" required>
        <input type="text" name="description" value="{role.description or ''}">
        <button type="submit">Сохранить</button>
    </form>
    <a href="/admin/roles">Отмена</a>
    """
    return HTMLResponse(content=html)

@router.post("/roles/edit/{role_id}", response_model=None)
async def edit_role(
    role_id: int,
    role_name: str = Form(...),
    description: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = RoleUpdate(role_name=role_name, description=description)
    await role_service.update_role(db, role_id, data)
    return RedirectResponse(url="/admin/roles", status_code=303)

@router.get("/roles/delete/{role_id}", response_class=HTMLResponse)
async def confirm_delete_role(role_id: int, db: AsyncSession = Depends(get_db)):
    role = await role_service.get_role(db, role_id)
    if not role:
        return HTMLResponse("Роль не найдена", status_code=404)
    html = f"""
    <h1>Удалить роль "{role.role_name}"?</h1>
    <form method="post" action="/admin/roles/delete/{role_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/roles">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/roles/delete/{role_id}", response_model=None)
async def delete_role(role_id: int, db: AsyncSession = Depends(get_db)):
    await role_service.delete_role(db, role_id)
    return RedirectResponse(url="/admin/roles", status_code=303)

@router.post("/roles/bulk-delete", response_model=None)
async def bulk_delete_roles(ids: List[int] = Form(...), db: AsyncSession = Depends(get_db)):
    await role_service.bulk_delete_roles(db, ids)
    return RedirectResponse(url="/admin/roles", status_code=303)

# ----- Права -----
@router.get("/permissions", response_class=HTMLResponse)
async def permissions_page(db: AsyncSession = Depends(get_db)):
    permissions = await permission_service.get_all_permissions(db)
    return HTMLResponse(content=render_permissions_html(permissions))

@router.post("/permissions/add", response_model=None)
async def add_permission(
    permission_code: str = Form(...),
    permission_name: str = Form(...),
    description: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = PermissionCreate(permission_code=permission_code, permission_name=permission_name, description=description)
    await permission_service.create_permission(db, data)
    return RedirectResponse(url="/admin/permissions", status_code=303)

@router.get("/permissions/edit/{perm_id}", response_class=HTMLResponse)
async def edit_permission_form(perm_id: int, db: AsyncSession = Depends(get_db)):
    perm = await permission_service.get_permission(db, perm_id)
    if not perm:
        return HTMLResponse("Право не найдено", status_code=404)
    html = f"""
    <h1>Редактировать право</h1>
    <form method="post" action="/admin/permissions/edit/{perm_id}">
        <input type="text" name="permission_code" value="{perm.permission_code}" required>
        <input type="text" name="permission_name" value="{perm.permission_name}" required>
        <input type="text" name="description" value="{perm.description or ''}">
        <button type="submit">Сохранить</button>
    </form>
    <a href="/admin/permissions">Отмена</a>
    """
    return HTMLResponse(content=html)

@router.post("/permissions/edit/{perm_id}", response_model=None)
async def edit_permission(
    perm_id: int,
    permission_code: str = Form(...),
    permission_name: str = Form(...),
    description: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    data = PermissionUpdate(permission_code=permission_code, permission_name=permission_name, description=description)
    await permission_service.update_permission(db, perm_id, data)
    return RedirectResponse(url="/admin/permissions", status_code=303)

@router.get("/permissions/delete/{perm_id}", response_class=HTMLResponse)
async def confirm_delete_permission(perm_id: int, db: AsyncSession = Depends(get_db)):
    perm = await permission_service.get_permission(db, perm_id)
    if not perm:
        return HTMLResponse("Право не найдено", status_code=404)
    html = f"""
    <h1>Удалить право "{perm.permission_name}"?</h1>
    <form method="post" action="/admin/permissions/delete/{perm_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/permissions">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/permissions/delete/{perm_id}", response_model=None)
async def delete_permission(perm_id: int, db: AsyncSession = Depends(get_db)):
    await permission_service.delete_permission(db, perm_id)
    return RedirectResponse(url="/admin/permissions", status_code=303)

@router.post("/permissions/bulk-delete", response_model=None)
async def bulk_delete_permissions(ids: List[int] = Form(...), db: AsyncSession = Depends(get_db)):
    await permission_service.bulk_delete_permissions(db, ids)
    return RedirectResponse(url="/admin/permissions", status_code=303)

# ----- Временные слоты -----
@router.get("/time-slots", response_class=HTMLResponse)
async def time_slots_page(db: AsyncSession = Depends(get_db)):
    time_slots = await time_slot_service.get_all_time_slots(db)
    return HTMLResponse(content=render_time_slots_html(time_slots))

@router.post("/time-slots/add", response_model=None)
async def add_time_slot(
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
    return RedirectResponse(url="/admin/time-slots", status_code=303)

@router.get("/time-slots/edit/{ts_id}", response_class=HTMLResponse)
async def edit_time_slot_form(ts_id: int, db: AsyncSession = Depends(get_db)):
    ts = await time_slot_service.get_time_slot(db, ts_id)
    if not ts:
        return HTMLResponse("Слот не найден", status_code=404)
    html = f"""
    <h1>Редактировать временной слот</h1>
    <form method="post" action="/admin/time-slots/edit/{ts_id}">
        <input type="number" name="slot_number" value="{ts.slot_number}" required>
        <input type="text" name="name" value="{ts.name}" required>
        <input type="time" name="start_time" value="{ts.start_time.isoformat()}" required>
        <input type="time" name="end_time" value="{ts.end_time.isoformat()}" required>
        <input type="number" name="duration_minutes" value="{ts.duration_minutes or ''}">
        <input type="number" name="break_after_minutes" value="{ts.break_after_minutes or ''}">
        <label><input type="checkbox" name="is_active" value="true" {'checked' if ts.is_active else ''}> Активен</label>
        <button type="submit">Сохранить</button>
    </form>
    <a href="/admin/time-slots">Отмена</a>
    """
    return HTMLResponse(content=html)

@router.post("/time-slots/edit/{ts_id}", response_model=None)
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
    return RedirectResponse(url="/admin/time-slots", status_code=303)

@router.get("/time-slots/delete/{ts_id}", response_class=HTMLResponse)
async def confirm_delete_time_slot(ts_id: int, db: AsyncSession = Depends(get_db)):
    ts = await time_slot_service.get_time_slot(db, ts_id)
    if not ts:
        return HTMLResponse("Слот не найден", status_code=404)
    html = f"""
    <h1>Удалить слот "{ts.name}"?</h1>
    <form method="post" action="/admin/time-slots/delete/{ts_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/time-slots">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/time-slots/delete/{ts_id}", response_model=None)
async def delete_time_slot(ts_id: int, db: AsyncSession = Depends(get_db)):
    await time_slot_service.delete_time_slot(db, ts_id)
    return RedirectResponse(url="/admin/time-slots", status_code=303)

@router.post("/time-slots/bulk-delete", response_model=None)
async def bulk_delete_time_slots(ids: List[int] = Form(...), db: AsyncSession = Depends(get_db)):
    await time_slot_service.bulk_delete_time_slots(db, ids)
    return RedirectResponse(url="/admin/time-slots", status_code=303)

# ----- Дисциплины -----
@router.get("/subjects", response_class=HTMLResponse)
async def subjects_page(db: AsyncSession = Depends(get_db)):
    subjects = await subject_service.get_all_subjects(db)
    return HTMLResponse(content=render_subjects_html(subjects))

@router.post("/subjects/add", response_model=None)
async def add_subject(
    name: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    data = SubjectCreate(name=name)
    await subject_service.create_subject(db, data)
    return RedirectResponse(url="/admin/subjects", status_code=303)

@router.get("/subjects/edit/{subject_id}", response_class=HTMLResponse)
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

@router.post("/subjects/edit/{subject_id}", response_model=None)
async def edit_subject(
    subject_id: int,
    name: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    data = SubjectUpdate(name=name)
    await subject_service.update_subject(db, subject_id, data)
    return RedirectResponse(url="/admin/subjects", status_code=303)

@router.get("/subjects/delete/{subject_id}", response_class=HTMLResponse)
async def confirm_delete_subject(subject_id: int, db: AsyncSession = Depends(get_db)):
    subject = await subject_service.get_subject(db, subject_id)
    if not subject:
        return HTMLResponse("Дисциплина не найдена", status_code=404)
    html = f"""
    <h1>Удалить дисциплину "{subject.name}"?</h1>
    <form method="post" action="/admin/subjects/delete/{subject_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/subjects">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/subjects/delete/{subject_id}", response_model=None)
async def delete_subject(subject_id: int, db: AsyncSession = Depends(get_db)):
    await subject_service.delete_subject(db, subject_id)
    return RedirectResponse(url="/admin/subjects", status_code=303)

@router.post("/subjects/bulk-delete", response_model=None)
async def bulk_delete_subjects(ids: List[int] = Form(...), db: AsyncSession = Depends(get_db)):
    await subject_service.bulk_delete_subjects(db, ids)
    return RedirectResponse(url="/admin/subjects", status_code=303)

# ----- Связь преподаватель-группа -----
@router.get("/teacher-groups", response_class=HTMLResponse)
async def teacher_groups_page(db: AsyncSession = Depends(get_db)):
    teachers = await teacher_service.get_all_teachers(db)
    groups = await group_service.get_all_groups(db)
    teacher_groups = await teacher_group_service.get_all_teacher_groups(db)
    return HTMLResponse(content=render_teacher_groups_html(teacher_groups, teachers, groups))

@router.post("/teacher-groups/add", response_model=None)
async def add_teacher_group(
    teacher_ids: List[int] = Form(...),
    group_ids: List[int] = Form(...),
    db: AsyncSession = Depends(get_db)
):
    added = 0
    skipped = 0
    for t_id in teacher_ids:
        for g_id in group_ids:
            result = await teacher_group_service.create_teacher_group(db, t_id, g_id)
            if result:
                added += 1
            else:
                skipped += 1
    return RedirectResponse(url="/admin/teacher-groups", status_code=303)

@router.post("/teacher-groups/bulk-delete", response_model=None)
async def bulk_delete_teacher_groups(ids: List[str] = Form(...), db: AsyncSession = Depends(get_db)):
    pairs = []
    for item in ids:
        parts = item.split(',')
        if len(parts) == 2:
            pairs.append((int(parts[0]), int(parts[1])))
    await teacher_group_service.bulk_delete_teacher_groups(db, pairs)
    return RedirectResponse(url="/admin/teacher-groups", status_code=303)

@router.get("/teacher-groups/delete/{teacher_id}/{group_id}", response_class=HTMLResponse)
async def confirm_delete_teacher_group(teacher_id: int, group_id: int, db: AsyncSession = Depends(get_db)):
    html = f"""
    <h1>Удалить связь преподавателя {teacher_id} и группы {group_id}?</h1>
    <form method="post" action="/admin/teacher-groups/delete/{teacher_id}/{group_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/teacher-groups">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/teacher-groups/delete/{teacher_id}/{group_id}", response_model=None)
async def delete_teacher_group(teacher_id: int, group_id: int, db: AsyncSession = Depends(get_db)):
    await teacher_group_service.delete_teacher_group(db, teacher_id, group_id)
    return RedirectResponse(url="/admin/teacher-groups", status_code=303)

# ----- Связь преподаватель-предмет -----
@router.get("/teacher-subjects", response_class=HTMLResponse)
async def teacher_subjects_page(db: AsyncSession = Depends(get_db)):
    teachers = await teacher_service.get_all_teachers(db)
    subjects = await subject_service.get_all_subjects(db)
    teacher_subjects = await teacher_subject_service.get_all_teacher_subjects(db)
    return HTMLResponse(content=render_teacher_subjects_html(teacher_subjects, teachers, subjects))

@router.post("/teacher-subjects/add", response_model=None)
async def add_teacher_subject(
    teacher_ids: List[int] = Form(...),
    subject_ids: List[int] = Form(...),
    is_main: bool = Form(False),
    db: AsyncSession = Depends(get_db)
):
    added = 0
    skipped = 0
    for t_id in teacher_ids:
        for s_id in subject_ids:
            result = await teacher_subject_service.create_teacher_subject(db, t_id, s_id, is_main)
            if result:
                added += 1
            else:
                skipped += 1
    return RedirectResponse(url="/admin/teacher-subjects", status_code=303)

@router.post("/teacher-subjects/bulk-delete", response_model=None)
async def bulk_delete_teacher_subjects(ids: List[str] = Form(...), db: AsyncSession = Depends(get_db)):
    pairs = []
    for item in ids:
        parts = item.split(',')
        if len(parts) == 2:
            pairs.append((int(parts[0]), int(parts[1])))
    await teacher_subject_service.bulk_delete_teacher_subjects(db, pairs)
    return RedirectResponse(url="/admin/teacher-subjects", status_code=303)

@router.get("/teacher-subjects/edit/{teacher_id}/{subject_id}", response_class=HTMLResponse)
async def edit_teacher_subject_form(teacher_id: int, subject_id: int, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app.models.reference import op_teachers_of_pairs
    result = await db.execute(
        select(op_teachers_of_pairs).where(
            op_teachers_of_pairs.c.teacher_id == teacher_id,
            op_teachers_of_pairs.c.subject_id == subject_id
        )
    )
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

@router.post("/teacher-subjects/edit/{teacher_id}/{subject_id}", response_model=None)
async def edit_teacher_subject(
    teacher_id: int, subject_id: int,
    is_main: bool = Form(False),
    db: AsyncSession = Depends(get_db)
):
    await teacher_subject_service.update_teacher_subject(db, teacher_id, subject_id, is_main)
    return RedirectResponse(url="/admin/teacher-subjects", status_code=303)

@router.get("/teacher-subjects/delete/{teacher_id}/{subject_id}", response_class=HTMLResponse)
async def confirm_delete_teacher_subject(teacher_id: int, subject_id: int, db: AsyncSession = Depends(get_db)):
    html = f"""
    <h1>Удалить связь преподавателя {teacher_id} и предмета {subject_id}?</h1>
    <form method="post" action="/admin/teacher-subjects/delete/{teacher_id}/{subject_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/teacher-subjects">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/teacher-subjects/delete/{teacher_id}/{subject_id}", response_model=None)
async def delete_teacher_subject(teacher_id: int, subject_id: int, db: AsyncSession = Depends(get_db)):
    await teacher_subject_service.delete_teacher_subject(db, teacher_id, subject_id)
    return RedirectResponse(url="/admin/teacher-subjects", status_code=303)

# ----- Связь аудитория-предмет -----
@router.get("/audience-subjects", response_class=HTMLResponse)
async def audience_subjects_page(db: AsyncSession = Depends(get_db)):
    audiences = await audience_service.get_all_audiences(db)
    subjects = await subject_service.get_all_subjects(db)
    audience_subjects = await audience_subject_service.get_all_audience_subjects(db)
    return HTMLResponse(content=render_audience_subjects_html(audience_subjects, audiences, subjects))

@router.post("/audience-subjects/add", response_model=None)
async def add_audience_subject(
    audience_ids: List[int] = Form(...),
    subject_ids: List[int] = Form(...),
    db: AsyncSession = Depends(get_db)
):
    added = 0
    skipped = 0
    for a_id in audience_ids:
        for s_id in subject_ids:
            result = await audience_subject_service.create_audience_subject(db, a_id, s_id)
            if result:
                added += 1
            else:
                skipped += 1
    return RedirectResponse(url="/admin/audience-subjects", status_code=303)

@router.post("/audience-subjects/bulk-delete", response_model=None)
async def bulk_delete_audience_subjects(ids: List[str] = Form(...), db: AsyncSession = Depends(get_db)):
    pairs = []
    for item in ids:
        parts = item.split(',')
        if len(parts) == 2:
            pairs.append((int(parts[0]), int(parts[1])))
    await audience_subject_service.bulk_delete_audience_subjects(db, pairs)
    return RedirectResponse(url="/admin/audience-subjects", status_code=303)

@router.get("/audience-subjects/delete/{audience_id}/{subject_id}", response_class=HTMLResponse)
async def confirm_delete_audience_subject(audience_id: int, subject_id: int, db: AsyncSession = Depends(get_db)):
    html = f"""
    <h1>Удалить связь аудитории {audience_id} и предмета {subject_id}?</h1>
    <form method="post" action="/admin/audience-subjects/delete/{audience_id}/{subject_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/audience-subjects">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/audience-subjects/delete/{audience_id}/{subject_id}", response_model=None)
async def delete_audience_subject(audience_id: int, subject_id: int, db: AsyncSession = Depends(get_db)):
    await audience_subject_service.delete_audience_subject(db, audience_id, subject_id)
    return RedirectResponse(url="/admin/audience-subjects", status_code=303)

# ----- Связь группа-предмет -----
@router.get("/group-subjects", response_class=HTMLResponse)
async def group_subjects_page(db: AsyncSession = Depends(get_db)):
    groups = await group_service.get_all_groups(db)
    subjects = await subject_service.get_all_subjects(db)
    group_subjects = await group_subject_service.get_all_group_subjects(db)
    return HTMLResponse(content=render_group_subjects_html(group_subjects, groups, subjects))

@router.post("/group-subjects/add", response_model=None)
async def add_group_subject(
    group_ids: List[int] = Form(...),
    subject_ids: List[int] = Form(...),
    db: AsyncSession = Depends(get_db)
):
    added = 0
    skipped = 0
    for g_id in group_ids:
        for s_id in subject_ids:
            result = await group_subject_service.create_group_subject(db, g_id, s_id)
            if result:
                added += 1
            else:
                skipped += 1
    return RedirectResponse(url="/admin/group-subjects", status_code=303)

@router.post("/group-subjects/bulk-delete", response_model=None)
async def bulk_delete_group_subjects(ids: List[str] = Form(...), db: AsyncSession = Depends(get_db)):
    pairs = []
    for item in ids:
        parts = item.split(',')
        if len(parts) == 2:
            pairs.append((int(parts[0]), int(parts[1])))
    await group_subject_service.bulk_delete_group_subjects(db, pairs)
    return RedirectResponse(url="/admin/group-subjects", status_code=303)

@router.get("/group-subjects/delete/{group_id}/{subject_id}", response_class=HTMLResponse)
async def confirm_delete_group_subject(group_id: int, subject_id: int, db: AsyncSession = Depends(get_db)):
    html = f"""
    <h1>Удалить связь группы {group_id} и предмета {subject_id}?</h1>
    <form method="post" action="/admin/group-subjects/delete/{group_id}/{subject_id}">
        <button type="submit">Да, удалить</button>
        <a href="/admin/group-subjects">Отмена</a>
    </form>
    """
    return HTMLResponse(content=html)

@router.post("/group-subjects/delete/{group_id}/{subject_id}", response_model=None)
async def delete_group_subject(group_id: int, subject_id: int, db: AsyncSession = Depends(get_db)):
    await group_subject_service.delete_group_subject(db, group_id, subject_id)
    return RedirectResponse(url="/admin/group-subjects", status_code=303)