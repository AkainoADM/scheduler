from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from app.routers.admin.common import _common_styles

router = APIRouter(prefix="/admin", tags=["Admin"])

# Импортируем все модули (они должны существовать)
from app.routers.admin import groups
from app.routers.admin import teachers
from app.routers.admin import audiences
from app.routers.admin import buildings
from app.routers.admin import calendar
from app.routers.admin import faculties
from app.routers.admin import users
from app.routers.admin import user_types
from app.routers.admin import subdivisions
from app.routers.admin import roles
from app.routers.admin import permissions
from app.routers.admin import time_slots
from app.routers.admin import subjects
from app.routers.admin import teacher_groups
from app.routers.admin import teacher_subjects
from app.routers.admin import audience_subjects
from app.routers.admin import group_subjects
from app.routers.admin import manual_schedule
from app.routers.admin import schedule_editor
from app.routers.admin import final_schedule
from app.routers.admin import stats
from app.routers.admin import logs

# Подключаем роутеры
router.include_router(groups.router)
router.include_router(teachers.router)
router.include_router(audiences.router)
router.include_router(buildings.router)
router.include_router(calendar.router)
router.include_router(faculties.router)
router.include_router(users.router)
router.include_router(user_types.router)
router.include_router(subdivisions.router)
router.include_router(roles.router)
router.include_router(permissions.router)
router.include_router(time_slots.router)
router.include_router(subjects.router)
router.include_router(teacher_groups.router)
router.include_router(teacher_subjects.router)
router.include_router(audience_subjects.router)
router.include_router(group_subjects.router)
router.include_router(manual_schedule.router)
router.include_router(schedule_editor.router)
router.include_router(final_schedule.router)
router.include_router(stats.router)
router.include_router(logs.router)

@router.get("", response_class=HTMLResponse)
async def admin_home():
    return HTMLResponse(content=f"""
    {_common_styles()}
    <h1>Административная панель</h1>
    <ul>
        <li><a href='/admin/groups'>Группы</a></li>
        <li><a href='/admin/teachers'>Преподаватели</a></li>
        <li><a href='/admin/audiences'>Аудитории</a></li>
        <li><a href='/admin/buildings'>Здания</a></li>
        <li><a href='/admin/calendar'>Календарь</a></li>
        <li><a href='/admin/faculties'>Факультеты</a></li>
        <li><a href='/admin/users'>Пользователи</a></li>
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
        <li><a href='/admin/manual-schedule'>Ручное составление расписания</a></li>
        <li><a href='/admin/schedule-editor'>Черновик расписания</a></li>
        <li><a href='/admin/final-schedule'>Опубликованное расписание</a></li>
        <li><a href='/admin/stats'>Статистика</a></li>
        <li><a href='/admin/logs'>Журнал действий</a></li>
    </ul>
    <a href='/'>На главную API</a>
    """)