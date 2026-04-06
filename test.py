from auth import get_password_hash
from database import SessionLocal
import models

db = SessionLocal()

# 1. Создаем роль, если её еще нет
admin_role = db.query(models.Role).filter(models.Role.role_name == "admin").first()
if not admin_role:
    admin_role = models.Role(role_name="admin")
    db.add(admin_role)
    db.commit()

# 2. Создаем пользователя
test_user = models.User(
    username="admin_test",
    email="admin@example.com",
    password_hash=get_password_hash("password123"), # Хешируем!
    is_active=True
)
db.add(test_user)
db.commit()

# 3. Назначаем роль
user_role = models.UserRole(user_id=test_user.id, role_id=admin_role.id)
db.add(user_role)
db.commit()
db.close()
print("Тестовый администратор создан: admin_test / password123")