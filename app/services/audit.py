import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.reference import UserActivityLog
from fastapi import Request

async def log_action(
    db: AsyncSession,
    action_type: str,
    action_details: dict,
    request: Request = None,
    user_id: int = None
):
    ip_address = None
    user_agent = None
    if request:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
    log = UserActivityLog(
        user_id=user_id,
        action_type=action_type,
        action_details=action_details,
        ip_address=ip_address,
        user_agent=user_agent,
        created_at=datetime.utcnow()
    )
    db.add(log)
    await db.commit()