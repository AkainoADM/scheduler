from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

Base = declarative_base()

_engine = None
_async_session_local = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(settings.DATABASE_URL, echo=True)
    return _engine

def get_async_session_local():
    global _async_session_local
    if _async_session_local is None:
        engine = get_engine()
        _async_session_local = async_sessionmaker(engine, expire_on_commit=False)
    return _async_session_local

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async_session_local = get_async_session_local()  # получаем фабрику сессий
    async with async_session_local() as session:    # вызываем фабрику для создания сессии
        yield session