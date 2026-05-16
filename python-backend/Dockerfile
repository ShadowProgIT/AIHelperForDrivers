# python-backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код
COPY . .

# Создаём папки для аудио (если их нет)
RUN mkdir -p audio_input audio_output chroma_db

# Порт
EXPOSE 8000

# Команда по умолчанию (будет переопределена в docker-compose.yml)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]