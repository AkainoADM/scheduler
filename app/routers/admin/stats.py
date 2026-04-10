from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import (
    group as group_service,
    teacher as teacher_service,
    audience as audience_service,
    building as building_service,
    calendar as calendar_service,
    faculty as faculty_service,
    user_type as user_type_service,
    subdivision as subdivision_service,
    role as role_service,
    permission as permission_service,
    time_slot as time_slot_service,
    subject as subject_service,
)
from app.services import teacher_group as teacher_group_service
from app.services import teacher_subject as teacher_subject_service
from app.services import audience_subject as audience_subject_service
from app.services import group_subject as group_subject_service
from app.routers.admin.common import _common_styles

router = APIRouter(prefix="/admin/stats", tags=["Admin Stats"])

@router.get("", response_class=HTMLResponse)
async def stats_page(db: AsyncSession = Depends(get_db)):
    groups_count = len(await group_service.get_all_groups(db))
    teachers_count = len(await teacher_service.get_all_teachers(db))
    audiences_count = len(await audience_service.get_all_audiences(db))
    buildings_count = len(await building_service.get_all_buildings(db))
    calendar_count = len(await calendar_service.get_all_calendar(db))
    faculties_count = len(await faculty_service.get_all_faculties(db))
    user_types_count = len(await user_type_service.get_all_user_types(db))
    subdivisions_count = len(await subdivision_service.get_all_subdivisions(db))
    roles_count = len(await role_service.get_all_roles(db))
    permissions_count = len(await permission_service.get_all_permissions(db))
    time_slots_count = len(await time_slot_service.get_all_time_slots(db))
    subjects_count = len(await subject_service.get_all_subjects(db))
    teacher_groups_count = len(await teacher_group_service.get_all_teacher_groups(db))
    teacher_subjects_count = len(await teacher_subject_service.get_all_teacher_subjects(db))
    audience_subjects_count = len(await audience_subject_service.get_all_audience_subjects(db))
    group_subjects_count = len(await group_subject_service.get_all_group_subjects(db))

    html = f"""
    <html>
    <head><title>Статистика системы</title>
    <style>
        body {{ font-family: sans-serif; margin: 20px; }}
        h1 {{ color: #2c3e50; }}
        .stats-container {{ display: flex; flex-wrap: wrap; gap: 20px; }}
        .card {{ background: #f8f9fa; border-radius: 8px; padding: 15px; width: 250px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .card h3 {{ margin: 0 0 10px; color: #3498db; }}
        .card .count {{ font-size: 32px; font-weight: bold; color: #2c3e50; }}
        hr {{ margin: 20px 0; }}
    </style>
    </head>
    <body>
        <h1>Статистика системы</h1>
        <div class='stats-container'>
            <div class='card'><h3>Группы</h3><div class='count'>{groups_count}</div></div>
            <div class='card'><h3>Преподаватели</h3><div class='count'>{teachers_count}</div></div>
            <div class='card'><h3>Аудитории</h3><div class='count'>{audiences_count}</div></div>
            <div class='card'><h3>Здания</h3><div class='count'>{buildings_count}</div></div>
            <div class='card'><h3>Календарь</h3><div class='count'>{calendar_count}</div></div>
            <div class='card'><h3>Факультеты</h3><div class='count'>{faculties_count}</div></div>
            <div class='card'><h3>Типы пользователей</h3><div class='count'>{user_types_count}</div></div>
            <div class='card'><h3>Подразделения</h3><div class='count'>{subdivisions_count}</div></div>
            <div class='card'><h3>Роли</h3><div class='count'>{roles_count}</div></div>
            <div class='card'><h3>Права</h3><div class='count'>{permissions_count}</div></div>
            <div class='card'><h3>Временные слоты</h3><div class='count'>{time_slots_count}</div></div>
            <div class='card'><h3>Дисциплины</h3><div class='count'>{subjects_count}</div></div>
        </div>
        <hr>
        <h2>Связи</h2>
        <div class='stats-container'>
            <div class='card'><h3>Преподаватели ↔ Группы</h3><div class='count'>{teacher_groups_count}</div></div>
            <div class='card'><h3>Преподаватели ↔ Предметы</h3><div class='count'>{teacher_subjects_count}</div></div>
            <div class='card'><h3>Аудитории ↔ Предметы</h3><div class='count'>{audience_subjects_count}</div></div>
            <div class='card'><h3>Группы ↔ Предметы</h3><div class='count'>{group_subjects_count}</div></div>
        </div>
        <br><a href='/admin/'>На главную админки</a>
    </body>
    </html>
    """
    return HTMLResponse(content=html)