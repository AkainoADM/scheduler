from fastapi import APIRouter
from app.api.v1.endpoints import groups, teachers, audiences, buildings

router = APIRouter(prefix="/api/v1")
router.include_router(groups.router)
router.include_router(teachers.router)
router.include_router(audiences.router)
router.include_router(buildings.router)