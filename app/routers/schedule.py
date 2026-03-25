from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Timetable, Discipline, Group, Audience, User
from ..utils import generate_schedule

router = APIRouter(prefix="/schedule", tags=["Schedule"])

@router.get("/dispatcher", response_class=HTMLResponse)
def view_dispatcher_schedule(db: Session = Depends(get_db)):
    items = db.query(Timetable).all()

    lessons_dict = {l.id: l for l in db.query(Discipline).all()}
    groups_dict = {g.id: g for g in db.query(Group).all()}
    rooms_dict = {r.id: r for r in db.query(Audience).all()}
    teachers_dict = {t.id: t for t in db.query(User).all()}

    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница"]
    html_blocks = ""

    for day in days:
        day_items = [i for i in items if i.day_of_week == day]  # type: ignore
        if not day_items:
            continue

        html_blocks += f"<div class='day-card'><h2 class='day-header'>{day}</h2>"

        pairs_numbers = sorted({i.lesson_number for i in day_items})
        for pair in pairs_numbers:
            pair_items = [i for i in day_items if i.lesson_number == pair]  # type: ignore
            html_blocks += f"<div class='pair-block'><div class='pair-title'>Пара {pair}</div><ul class='parallel-list'>"

            for item in pair_items:
                lsn = lessons_dict.get(item.discipline_id)
                grp = groups_dict.get(item.group_id)
                rm = rooms_dict.get(item.audience_id)
                tchr = teachers_dict.get(lsn.teacher_id) if lsn else None

                subj_name = lsn.name if lsn else "---"
                grp_name = grp.name if grp else "---"
                rm_name = rm.name if rm else "---"
                tchr_name = tchr.full_name if tchr else "---"

                html_blocks += f"<li><strong>{subj_name}</strong> | Ауд. {rm_name} | Группа {grp_name} | {tchr_name}</li>"

            html_blocks += "</ul></div>"

        html_blocks += "</div>"

    content_block = html_blocks if html_blocks else '<p>Расписание пусто</p>'
    html_response = """
    <!DOCTYPE html>
    <html lang='ru'>
    <head>
        <meta charset='UTF-8'>
        <title>Панель диспетчера расписания</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #eef2f5; padding: 20px; color: #333; }
            .container { max-width: 900px; margin: 0 auto; }
            .header { display: flex; justify-content: space-between; align-items: center; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
            .btn { background: #0056b3; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 16px; font-weight: bold; }
            .btn:hover { background: #004494; }
            .day-card { background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
            .day-header { color: #d9534f; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-top: 0; }
            .pair-block { margin-bottom: 15px; border-left: 4px solid #5bc0de; padding-left: 15px; }
            .pair-title { font-weight: bold; color: #5bc0de; font-size: 1.1em; margin-bottom: 5px; }
            .parallel-list { list-style-type: none; padding: 0; margin: 0; }
            .parallel-list li { background: #f9f9f9; margin-bottom: 5px; padding: 8px 12px; border-radius: 4px; border: 1px solid #eaeaea; }
            .parallel-list strong { color: #333; }
        </style>
    </head>
    <body>
        <div class='container'>
            <div class='header'>
                <h1>📋 Панель диспетчера расписания</h1>
                <button class='btn' onclick="fetch('/api/generate', {method:'POST'}).then(()=>location.reload())">Сгенерировать новое</button>
            </div>
    """
    html_response += content_block
    html_response += """
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=html_response)
