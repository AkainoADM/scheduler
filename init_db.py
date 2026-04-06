import os
import models, auth, database
from database import SessionLocal, engine
import bcrypt
if not hasattr(bcrypt, "__about__"):
    bcrypt.__about__ = type('About', (object,), {'__version__': bcrypt.__version__}) # type: ignore
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
from dotenv import load_dotenv 


load_dotenv()

# Настройки
SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# ИСПРАВЛЕНИЕ ЗДЕСЬ:
# Явно задаем использование bcrypt через современный интерфейс
pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto",
    bcrypt__ident="2b" # Явно указываем идентификатор версии для совместимости
)

def get_password_hash(password: str):
    # Дополнительная страховка: кодируем в utf-8
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
def init():
    # Создаем таблицы, если их еще нет
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 1. Добавляем роли безопасно
        for r_name in ["admin", "scheduler"]:
            existing_role = db.query(models.Role).filter(models.Role.role_name == r_name).first()
            if not existing_role:
                db.add(models.Role(role_name=r_name))
                print(f"Роль '{r_name}' создана.")
        
        db.commit() # Сохраняем роли, чтобы получить их ID

        # 2. Добавляем пользователя безопасно
        username = "admin_test"
        existing_user = db.query(models.User).filter(models.User.username == username).first()
        
        if not existing_user:
            admin_role = db.query(models.Role).filter(models.Role.role_name == "admin").one()
            
            hashed_pwd = auth.get_password_hash("password123")
            new_user = models.User(
                username=username, 
                email="admin@test.ru", 
                password_hash=hashed_pwd
            )
            db.add(new_user)
            db.commit() # Сначала сохраняем пользователя

            # Привязываем роль
            user_role = models.UserRole(user_id=new_user.id, role_id=admin_role.id)
            db.add(user_role)
            db.commit()
            print(f"Пользователь '{username}' создан и наделен правами админа.")
        else:
            print(f"Пользователь '{username}' уже существует, пропускаем.")

    except Exception as e:
        db.rollback()
        print(f"Произошла ошибка: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init()