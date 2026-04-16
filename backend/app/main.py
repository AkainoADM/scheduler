# app/main.py
from fastapi import FastAPI
from app.api.v1 import endpoints
from app.api.routers import router as api_router 
from fastapi.middleware.cors import CORSMiddleware
import os
from datetime import date
from typing import List
from fastapi import FastAPI, Depends, Form, Request, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.api.v1 import router as v1_router
from app.core.database import get_db
from app.services import calendar_sync
from app.schemas.calendar import CalendarCreate, CalendarUpdate
from app.services import calendar as calendar_service

app = FastAPI(title="Schedule MVP")
app.include_router(api_router)
app = FastAPI(title="Schedule MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app = FastAPI(title="Schedule Generation System")
app.include_router(v1_router)

@app.get("/")
async def root():
    return {
        "message": "Schedule Generation System API",
        "docs": "/docs",
        "admin_panel": "/admin",
        "redoc": "/redoc"
    }

@app.get("/db-check")
async def db_check(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT version()"))
    version = result.scalar()
    return {"postgres_version": version}

# Прокси на старый сервер (оставьте, если нужно)
import httpx

@app.get("/generate-schedule")
async def generate_schedule():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post("http://localhost:8001/api/generate", timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))

@app.get("/get-schedule-old")
async def get_schedule_old():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8001/api/schedule", timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Старый сервер генерации недоступен: {e}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=500, detail=f"Ошибка получения расписания: {e.response.text}")

@app.get("/my-schedule-old", response_class=HTMLResponse)
async def my_schedule_old(request: Request):
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8001/api/schedule")
        data = response.json()
    html = "<h1>Расписание (старое)</h1>"
    if not data:
        html += "<p>Расписание пусто. Сначала сгенерируйте его.</p>"
    else:
        html += "<table border='1'><tr><th>Предмет</th><th>Преподаватель</th><th>Аудитория</th><th>Дата</th><th>Пара</th><th>Время</th></tr>"
        for row in data:
            html += f"<tr><td>{row['subject']}</td><td>{row['teacher']}</td><td>{row['audience']}</td><td>{row['date']}</td><td>{row['pair']}</td><td>{row['time']}</td></tr>"
        html += "</table>"
    html += "<p><a href='/'>На главную</a></p>"
    return HTMLResponse(content=html)