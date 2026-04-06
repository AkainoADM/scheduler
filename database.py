import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("postgresql://postgres:password@localhost:5432/schedule")
SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret_for_dev_only")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    print(f"ПРЕДУПРЕЖДЕНИЕ: Файл .env не найден по пути {dotenv_path}")

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    # Выведем список всех переменных, которые видит система (для отладки)
    print("Доступные переменные:", list(os.environ.keys()))
    raise ValueError("ОШИБКА: Переменная DATABASE_URL не найдена. Проверьте файл .env!")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

raw_expire = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
# Гарантируем, что это строка, прежде чем совать в int()
ACCESS_TOKEN_EXPIRE_MINUTES = int(raw_expire) if raw_expire else 30
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
