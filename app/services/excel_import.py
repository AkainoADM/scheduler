import io
from typing import List, Dict, Any
from openpyxl import load_workbook
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reference import Group, Teacher, Audience, Building, Faculty
from app.schemas.group import GroupUploadRow
from app.schemas.teacher import TeacherUploadRow
from app.schemas.audience import AudienceUploadRow
from app.schemas.building import BuildingUploadRow

# ---------- Группы ----------
async def parse_groups_excel(file_content: bytes) -> List[Dict[str, Any]]:
    wb = load_workbook(filename=io.BytesIO(file_content))
    ws = wb.active
    headers = [cell.value for cell in ws[1]]
    expected_columns = ['name', 'faculty_id', 'student_count']
    col_idx = {col: idx for idx, col in enumerate(headers) if col in expected_columns}
    rows = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not any(row):
            continue
        row_data = {}
        for col_name, idx in col_idx.items():
            row_data[col_name] = row[idx]
        rows.append(row_data)
    return rows

async def validate_groups_data(rows: List[Dict[str, Any]], db: AsyncSession) -> tuple[List[GroupUploadRow], List[Dict]]:
    valid_rows = []
    errors = []
    faculty_ids = set()
    for row in rows:
        if row.get('faculty_id') is not None:
            faculty_ids.add(row['faculty_id'])
    existing_faculty_ids = set()
    if faculty_ids:
        result = await db.execute(select(Faculty.id).where(Faculty.id.in_(faculty_ids)))
        existing_faculty_ids = {r[0] for r in result.all()}
    for idx, row in enumerate(rows, start=2):
        try:
            validated = GroupUploadRow(
                name=row.get('name'),
                faculty_id=row.get('faculty_id'),
                student_count=row.get('student_count')
            )
            if validated.faculty_id not in existing_faculty_ids:
                errors.append({"row": idx, "error": f"Факультет с id={validated.faculty_id} не найден"})
                continue
            valid_rows.append(validated)
        except Exception as e:
            errors.append({"row": idx, "error": str(e)})
    return valid_rows, errors

async def save_groups_from_validated(valid_rows: List[GroupUploadRow], db: AsyncSession) -> Dict[str, int]:
    added = 0
    updated = 0
    for row in valid_rows:
        stmt = select(Group).where(Group.name == row.name)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            existing.faculty_id = row.faculty_id
            existing.student_count = row.student_count
            updated += 1
        else:
            group = Group(name=row.name, faculty_id=row.faculty_id, student_count=row.student_count)
            db.add(group)
            added += 1
    await db.commit()
    return {"added": added, "updated": updated}

# ---------- Преподаватели ----------
async def parse_teachers_excel(file_content: bytes) -> List[Dict[str, Any]]:
    wb = load_workbook(filename=io.BytesIO(file_content))
    ws = wb.active
    headers = [cell.value for cell in ws[1]]
    expected_columns = ['login', 'name', 'url', 'max_hours_per_day', 'max_hours_per_week']
    col_idx = {col: idx for idx, col in enumerate(headers) if col in expected_columns}
    rows = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not any(row):
            continue
        row_data = {}
        for col_name, idx in col_idx.items():
            row_data[col_name] = row[idx]
        rows.append(row_data)
    return rows

async def validate_teachers_data(rows: List[Dict[str, Any]], db: AsyncSession) -> tuple[List[TeacherUploadRow], List[Dict]]:
    valid_rows = []
    errors = []
    for idx, row in enumerate(rows, start=2):
        try:
            validated = TeacherUploadRow(
                login=row.get('login'),
                name=row.get('name'),
                url=row.get('url'),
                max_hours_per_day=row.get('max_hours_per_day'),
                max_hours_per_week=row.get('max_hours_per_week')
            )
            valid_rows.append(validated)
        except Exception as e:
            errors.append({"row": idx, "error": str(e)})
    return valid_rows, errors

async def save_teachers_from_validated(valid_rows: List[TeacherUploadRow], db: AsyncSession) -> Dict[str, int]:
    added = 0
    updated = 0
    for row in valid_rows:
        stmt = select(Teacher).where(Teacher.login == row.login)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            existing.name = row.name
            existing.url = row.url
            existing.max_hours_per_day = row.max_hours_per_day
            existing.max_hours_per_week = row.max_hours_per_week
            updated += 1
        else:
            teacher = Teacher(
                login=row.login,
                name=row.name,
                url=row.url,
                max_hours_per_day=row.max_hours_per_day,
                max_hours_per_week=row.max_hours_per_week
            )
            db.add(teacher)
            added += 1
    await db.commit()
    return {"added": added, "updated": updated}

# ---------- Аудитории ----------
async def parse_audiences_excel(file_content: bytes) -> List[Dict[str, Any]]:
    wb = load_workbook(filename=io.BytesIO(file_content))
    ws = wb.active
    headers = [cell.value for cell in ws[1]]
    expected_columns = ['name', 'building_id', 'capacity', 'type', 'is_active']
    col_idx = {col: idx for idx, col in enumerate(headers) if col in expected_columns}
    rows = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not any(row):
            continue
        row_data = {}
        for col_name, idx in col_idx.items():
            row_data[col_name] = row[idx]
        rows.append(row_data)
    return rows

async def validate_audiences_data(rows: List[Dict[str, Any]], db: AsyncSession) -> tuple[List[AudienceUploadRow], List[Dict]]:
    valid_rows = []
    errors = []
    building_ids = set()
    for row in rows:
        if row.get('building_id') is not None:
            building_ids.add(row['building_id'])
    existing_buildings = set()
    if building_ids:
        result = await db.execute(select(Building.id).where(Building.id.in_(building_ids)))
        existing_buildings = {r[0] for r in result.all()}
    for idx, row in enumerate(rows, start=2):
        try:
            validated = AudienceUploadRow(
                name=row.get('name'),
                building_id=row.get('building_id'),
                capacity=row.get('capacity'),
                type=row.get('type'),
                is_active=row.get('is_active', True)
            )
            if validated.building_id is not None and validated.building_id not in existing_buildings:
                errors.append({"row": idx, "error": f"Здание с id={validated.building_id} не найдено"})
                continue
            valid_rows.append(validated)
        except Exception as e:
            errors.append({"row": idx, "error": str(e)})
    return valid_rows, errors

async def save_audiences_from_validated(valid_rows: List[AudienceUploadRow], db: AsyncSession) -> Dict[str, int]:
    added = 0
    updated = 0
    for row in valid_rows:
        stmt = select(Audience).where(Audience.name == row.name)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            existing.building_id = row.building_id
            existing.capacity = row.capacity
            existing.type = row.type
            existing.is_active = row.is_active
            updated += 1
        else:
            audience = Audience(
                name=row.name,
                building_id=row.building_id,
                capacity=row.capacity,
                type=row.type,
                is_active=row.is_active
            )
            db.add(audience)
            added += 1
    await db.commit()
    return {"added": added, "updated": updated}

# ---------- Здания ----------
async def parse_buildings_excel(file_content: bytes) -> List[Dict[str, Any]]:
    wb = load_workbook(filename=io.BytesIO(file_content))
    ws = wb.active
    headers = [cell.value for cell in ws[1]]
    expected_columns = ['name', 'address']
    col_idx = {col: idx for idx, col in enumerate(headers) if col in expected_columns}
    rows = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not any(row):
            continue
        row_data = {}
        for col_name, idx in col_idx.items():
            row_data[col_name] = row[idx]
        rows.append(row_data)
    return rows

async def validate_buildings_data(rows: List[Dict[str, Any]], db: AsyncSession) -> tuple[List[BuildingUploadRow], List[Dict]]:
    valid_rows = []
    errors = []
    for idx, row in enumerate(rows, start=2):
        try:
            validated = BuildingUploadRow(
                name=row.get('name'),
                address=row.get('address')
            )
            valid_rows.append(validated)
        except Exception as e:
            errors.append({"row": idx, "error": str(e)})
    return valid_rows, errors

async def save_buildings_from_validated(valid_rows: List[BuildingUploadRow], db: AsyncSession) -> Dict[str, int]:
    added = 0
    updated = 0
    for row in valid_rows:
        stmt = select(Building).where(Building.name == row.name)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            existing.address = row.address
            updated += 1
        else:
            building = Building(name=row.name, address=row.address)
            db.add(building)
            added += 1
    await db.commit()
    return {"added": added, "updated": updated}