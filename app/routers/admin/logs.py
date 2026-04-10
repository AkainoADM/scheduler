import json
from datetime import datetime
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.reference import UserActivityLog
from app.routers.admin.common import export_to_excel, _common_styles

router = APIRouter(prefix="/admin/logs", tags=["Admin Logs"])

@router.get("", response_class=HTMLResponse)
async def logs_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    action: str = None,
    user_id: int = None,
    date_from: str = None,
    date_to: str = None
):
    query = select(UserActivityLog).order_by(UserActivityLog.created_at.desc())
    if action:
        query = query.where(UserActivityLog.action_type == action)
    if user_id:
        query = query.where(UserActivityLog.user_id == user_id)
    if date_from:
        query = query.where(UserActivityLog.created_at >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.where(UserActivityLog.created_at <= datetime.fromisoformat(date_to))
    result = await db.execute(query)
    logs = result.scalars().all()

    actions_result = await db.execute(select(UserActivityLog.action_type).distinct())
    actions = [row[0] for row in actions_result.all()]

    html = f"""
    <html>
    <head>
        <title>Журнал действий</title>
        {_common_styles()}
        <style>
            .filter-form {{ margin-bottom: 20px; }}
            .filter-form input, .filter-form select {{ margin-right: 10px; }}
        </style>
    </head>
    <body>
        <h1>Журнал действий</h1>
        <form method="get" class="filter-form">
            <select name="action">
                <option value="">Все действия</option>
                {''.join(f'<option value="{a}" {"selected" if action == a else ""}>{a}</option>' for a in actions)}
            </select>
            <input type="date" name="date_from" value="{date_from or ''}" placeholder="Дата от">
            <input type="date" name="date_to" value="{date_to or ''}" placeholder="Дата до">
            <button type="submit">Фильтр</button>
            <a href="/admin/logs">Сбросить</a>
        </form>
        <div><a href="/admin/logs/export" class="btn-excel">📎 Экспорт в Excel</a></div>
        <table border="1" style="width:100%; margin-top:20px;">
            <thead>
                <tr><th>ID</th><th>Время</th><th>Действие</th><th>Детали</th><th>IP</th><th>User Agent</th></tr>
            </thead>
            <tbody>
    """
    for log in logs:
        html += f"""
            <tr>
                <td>{log.id}</td>
                <td>{log.created_at}</td>
                <td>{log.action_type}</td>
                <td><pre>{json.dumps(log.action_details, ensure_ascii=False, indent=2)}</pre></td>
                <td>{log.ip_address or ''}</td>
                <td>{log.user_agent or ''}</td>
            </tr>
        """
    html += """
            </tbody>
        </table>
        <br><a href="/admin/">На главную админки</a>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@router.get("/export")
async def export_logs(db: AsyncSession = Depends(get_db)):
    logs = await db.execute(select(UserActivityLog).order_by(UserActivityLog.created_at))
    logs = logs.scalars().all()
    data = []
    for log in logs:
        data.append({
            "ID": log.id,
            "Время": log.created_at,
            "Действие": log.action_type,
            "Детали": json.dumps(log.action_details, ensure_ascii=False),
            "IP": log.ip_address or "",
            "User Agent": log.user_agent or "",
        })
    columns = ["ID", "Время", "Действие", "Детали", "IP", "User Agent"]
    return export_to_excel(data, columns, "Логи действий", "audit_logs.xlsx")