import os
from fastapi import FastAPI, Depends, Form
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
from app.schemas.group import GroupCreate, GroupUpdate
from app.schemas.teacher import TeacherCreate, TeacherUpdate
from app.schemas.audience import AudienceCreate, AudienceUpdate
from app.schemas.building import BuildingCreate, BuildingUpdate

app = FastAPI(title="Schedule Generation System")
app.include_router(v1_router)

# ---------- Вспомогательные функции для рендеринга ----------
def render_groups_html(groups, faculties):
    html = "<h1>Группы</h1>"
    html += "<form method='post' action='/groups/add'>"
    html += "<input type='text' name='name' placeholder='Название группы' required>"
    html += "<select name='faculty_id' required><option value=''>Выберите факультет</option>"
    for fac in faculties:
        html += f"<option value='{fac.id}'>{fac.name}</option>"
    html += "</select>"
    html += "<input type='number' name='student_count' placeholder='Количество студентов'>"
    html += "<button type='submit'>Добавить</button>"
    html += "</form>"
    html += "<ul>"
    for g in groups:
        html += f"<li>{g.name} (Факультет ID: {g.faculty_id}, Студентов: {g.student_count}) "
        html += f"<a href='/groups/edit/{g.id}'>Редактировать</a> "
        html += f"<a href='/groups/delete/{g.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "<a href='/'>На главную</a>"
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
    html += "<ul>"
    for t in teachers:
        html += f"<li>{t.name} (Логин: {t.login}, День: {t.max_hours_per_day or 'нет'}, Неделя: {t.max_hours_per_week or 'нет'}) "
        html += f"<a href='/teachers/edit/{t.id}'>Редактировать</a> "
        html += f"<a href='/teachers/delete/{t.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "<a href='/'>На главную</a>"
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
    html += "<ul>"
    for a in audiences:
        html += f"<li>{a.name} (Корпус ID: {a.building_id or 'не указан'}, Мест: {a.capacity or 'не указано'}, Тип: {a.type or 'не указан'}, Активна: {a.is_active}) "
        html += f"<a href='/audiences/edit/{a.id}'>Редактировать</a> "
        html += f"<a href='/audiences/delete/{a.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "<a href='/'>На главную</a>"
    return html

def render_buildings_html(buildings):
    html = "<h1>Здания</h1>"
    html += "<form method='post' action='/buildings/add'>"
    html += "<input type='text' name='name' placeholder='Название здания' required>"
    html += "<input type='text' name='address' placeholder='Адрес'>"
    html += "<button type='submit'>Добавить</button>"
    html += "</form>"
    html += "<ul>"
    for b in buildings:
        html += f"<li>{b.name} (Адрес: {b.address or 'не указан'}) "
        html += f"<a href='/buildings/edit/{b.id}'>Редактировать</a> "
        html += f"<a href='/buildings/delete/{b.id}'>Удалить</a></li>"
    html += "</ul>"
    html += "<a href='/'>На главную</a>"
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
        <li><a href='/docs'>Swagger API</a></li>
    </ul>
    """)

# ----- Группы -----
@app.get("/groups", response_class=HTMLResponse)
async def groups_page(db: AsyncSession = Depends(get_db)):
    groups = await group_service.get_all_groups(db)
    faculties = await faculty_service.get_all_faculties(db)
    return HTMLResponse(content=render_groups_html(groups, faculties))

@app.post("/groups/add")
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

@app.post("/groups/edit/{group_id}")
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

@app.post("/groups/delete/{group_id}")
async def delete_group(group_id: int, db: AsyncSession = Depends(get_db)):
    await group_service.delete_group(db, group_id)
    return RedirectResponse(url="/groups", status_code=303)

# ----- Преподаватели -----
@app.get("/teachers", response_class=HTMLResponse)
async def teachers_page(db: AsyncSession = Depends(get_db)):
    teachers = await teacher_service.get_all_teachers(db)
    return HTMLResponse(content=render_teachers_html(teachers))

@app.post("/teachers/add")
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

@app.post("/teachers/edit/{teacher_id}")
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

@app.post("/teachers/delete/{teacher_id}")
async def delete_teacher(teacher_id: int, db: AsyncSession = Depends(get_db)):
    await teacher_service.delete_teacher(db, teacher_id)
    return RedirectResponse(url="/teachers", status_code=303)

# ----- Аудитории -----
@app.get("/audiences", response_class=HTMLResponse)
async def audiences_page(db: AsyncSession = Depends(get_db)):
    audiences = await audience_service.get_all_audiences(db)
    buildings = await building_service.get_all_buildings(db)
    return HTMLResponse(content=render_audiences_html(audiences, buildings))

@app.post("/audiences/add")
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

@app.post("/audiences/edit/{audience_id}")
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

@app.post("/audiences/delete/{audience_id}")
async def delete_audience(audience_id: int, db: AsyncSession = Depends(get_db)):
    await audience_service.delete_audience(db, audience_id)
    return RedirectResponse(url="/audiences", status_code=303)

# ----- Здания -----
@app.get("/buildings", response_class=HTMLResponse)
async def buildings_page(db: AsyncSession = Depends(get_db)):
    buildings = await building_service.get_all_buildings(db)
    return HTMLResponse(content=render_buildings_html(buildings))

@app.post("/buildings/add")
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

@app.post("/buildings/edit/{building_id}")
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

@app.post("/buildings/delete/{building_id}")
async def delete_building(building_id: int, db: AsyncSession = Depends(get_db)):
    await building_service.delete_building(db, building_id)
    return RedirectResponse(url="/buildings", status_code=303)

# ========== Тестовый эндпоинт ==========
@app.get("/db-check")
async def db_check(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT version()"))
    version = result.scalar()
    return {"postgres_version": version}