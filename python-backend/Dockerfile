# python-backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Открываем порт
EXPOSE 8000

# Команда запуска (замените на вашу)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]