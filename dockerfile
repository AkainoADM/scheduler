# Используем легковесный образ Python 3.12
FROM python:3.12-slim

# Устанавливаем системные зависимости для сборки bcrypt и psycopg2
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей (если есть requirements.txt)
# Если нет, создадим его командой ниже
COPY requirements.txt .

# Устанавливаем библиотеки
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект в контейнер
COPY . .

# Открываем порт для FastAPI
EXPOSE 8000

# Команда для запуска (используем 0.0.0.0, чтобы достучаться извне контейнера)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]