from fastapi import APIRouter
from app.api.v1.endpoints import (
    groups, teachers, audiences, buildings,
    permissions, roles, subdivisions, time_slots, user_types, calendar, users, faculties
)

router = APIRouter(prefix="/api/v1")
router.include_router(groups.router)
router.include_router(teachers.router)
router.include_router(audiences.router)
router.include_router(buildings.router)
router.include_router(permissions.router)
router.include_router(roles.router)
router.include_router(subdivisions.router)
router.include_router(time_slots.router)
router.include_router(user_types.router)
router.include_router(users.router)
router.include_router(faculties.router)
router.include_router(calendar.router)
