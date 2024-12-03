# Используем официальный образ Python
FROM python:3.12.4-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Устанавливаем зависимости для PostgreSQL (необходимы для psycopg2)
RUN apt-get update && apt-get install -y libpq-dev

# Копируем и устанавливаем зависимости из requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем всё приложение
COPY . .

# Открываем порт, на котором будет работать FastAPI
EXPOSE 8001

CMD ["sh", "-c", "alembic upgrade head && exec python -m main"]
