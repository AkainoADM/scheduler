from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .database import engine, Base
from .routers import api, schedule

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RASPISANIE API",
    description="Система генерации расписания",
    version="1.0.0"
)

app.include_router(api.router)
app.include_router(schedule.router)

@app.get("/")
def root():
    return {"message": "Welcome to RASPISANIE API", "docs": "/docs"}