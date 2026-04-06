from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt, JWTError
import os
import models, auth, database
from database import get_db
from fastapi.staticfiles import StaticFiles # Для работы со статикой
from fastapi.responses import FileResponse  # Для отправки HTML-файла

app = FastAPI()


# Получаем путь к текущей директории, где лежит main.py
current_dir = os.path.dirname(os.path.realpath(__file__))
# 1. Настройка CORS (уже должна быть у вас)
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Подключаем папку со статикой (JS, CSS, картинки)
# Она будет доступна по адресу /static
app.mount("/static", StaticFiles(directory="static"), name="static")

# НАСТРОЙКА CORS: разрешаем браузеру обращаться к API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # В продакшене лучше указать конкретный адрес
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app = FastAPI(title="Schedule Management System")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

SECRET_KEY = os.getenv("SECRET_KEY", "super_secret_key_for_dev")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
    )
    try:
        # Теперь Pylance спокоен, так как SECRET_KEY и ALGORITHM — это гарантированно строки
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Убираем жесткую аннотацию ": str", позволяя переменной быть "Any | None"
        # Мы все равно проверяем её на None на следующей строке
        username = payload.get("sub")
        
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user
# Проверка роли "Администратор"
def check_admin_role(user: models.User = Depends(get_current_user)):
    roles = [r.role_name for r in user.roles]
    if "admin" not in roles:
        raise HTTPException(status_code=403, detail="Доступ запрещен: требуется роль Администратора")
    return user

# Проверка роли "Составитель расписания"
def check_scheduler_role(user: models.User = Depends(get_current_user)):
    roles = [r.role_name for r in user.roles]
    if "scheduler" not in roles and "admin" not in roles:
        raise HTTPException(status_code=403, detail="Доступ запрещен: требуется роль Составителя")
    return user

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, str(user.password_hash)):
        raise HTTPException(status_code=400, detail="Неверный логин или пароль")
    
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}
@app.get("/")
async def read_index():
    file_path = os.path.join(current_dir, "static", "index.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": f"Файл не найден по пути: {file_path}"}
@app.get("/admin/panel", dependencies=[Depends(check_admin_role)])
def admin_only_data():
    return {"message": "Добро пожаловать, Администратор!"}

@app.post("/schedule/create", dependencies=[Depends(check_scheduler_role)])
def create_schedule_item():
    return {"message": "Расписание успешно отредактировано"}