from fastapi import APIRouter
from app.api.v1.endpoints import (
    groups, teachers, audiences, buildings, calendar, faculties,
    user_types, subdivisions, roles, permissions, time_slots, subjects
)

router = APIRouter(prefix="/api/v1")
router.include_router(groups.router)
router.include_router(teachers.router)
router.include_router(audiences.router)
router.include_router(buildings.router)
router.include_router(calendar.router)
router.include_router(faculties.router)
router.include_router(user_types.router)
router.include_router(subdivisions.router)
router.include_router(roles.router)
router.include_router(permissions.router)
router.include_router(time_slots.router)
router.include_router(subjects.router)

# Если файл generation.py существует, раскомментируйте:
from app.api.v1.endpoints import generation
router.include_router(generation.router)


#from app.api.v1.endpoints import template_names, template_items

#router.include_router(template_names.router)
#router.include_router(template_items.router)

from app.api.v1.endpoints import days_of_week
router.include_router(days_of_week.router)


from app.api.v1.endpoints import teacher_groups, teacher_subjects, audience_subjects, group_subjects

router.include_router(teacher_groups.router)
router.include_router(teacher_subjects.router)
router.include_router(audience_subjects.router)
router.include_router(group_subjects.router)