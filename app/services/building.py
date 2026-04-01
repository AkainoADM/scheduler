from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.reference import Building
from app.schemas.building import BuildingCreate, BuildingUpdate
from typing import List
from sqlalchemy import select, update, delete
from app.models.reference import Building
from app.schemas.building import BuildingCreate, BuildingUpdate

# ... функции
async def bulk_delete_buildings(db: AsyncSession, ids: List[int]) -> None:
    await db.execute(delete(Building).where(Building.id.in_(ids)))
    await db.commit()
    
async def get_all_buildings(db: AsyncSession):
    result = await db.execute(select(Building))
    return result.scalars().all()

async def get_building(db: AsyncSession, building_id: int):
    result = await db.execute(select(Building).where(Building.id == building_id))
    return result.scalar_one_or_none()

async def create_building(db: AsyncSession, data: BuildingCreate) -> Building:
    building = Building(**data.model_dump())
    db.add(building)
    await db.commit()
    await db.refresh(building)
    return building

async def update_building(db: AsyncSession, building_id: int, data: BuildingUpdate) -> Building | None:
    stmt = update(Building).where(Building.id == building_id).values(**data.model_dump(exclude_unset=True)).returning(Building)
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one_or_none()

async def delete_building(db: AsyncSession, building_id: int) -> None:
    await db.execute(delete(Building).where(Building.id == building_id))
    await db.commit()

async def bulk_delete_buildings(db: AsyncSession, ids: List[int]) -> None:
    await db.execute(delete(Building).where(Building.id.in_(ids)))
    await db.commit()