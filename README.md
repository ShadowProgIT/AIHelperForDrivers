# Контракт. Структура JSON для обмена backend с AI 
{
    "sessionId": "session ID",
    "requestMode": "theory/practice",
    "content": "текст запроса пользователя",
    "image_url": "относительная ссылка на файл изображения"
}

# Контракт. Префикс для хранения java-сессий в Redis
backend:session

# Запуск проекта. Команды для запуска проекта
1. mvn clean install
2. mvn spring-boot:run -pl api-realisation

# Развёртывание модели. PowerShell, Docker. Команды
Создаёшь папки на диске. в driving-ai файл docker-compose.yml

# Контейнеризация. Команды в Docker
docker compose up -d 

docker exec -it ollama-server sh (зайти в оламу в ней работать)
ollama create qwen3.5-driving -f /Modelfile (уже в bash-е внутри оламы)

ollama list (проверка наличия модели qwen в ollama)

Порты:
Redis - 6379
Python - 8000

# **Endpoint:** `POST /api/ai-process`  
# **Content-Type:** `application/json`

json
{
  "sessionId": "string",
  "requestMode": "theory" | "practice",
  "content": "string",
  "image_url": "string | null"
}


# Продумать.
1. В Redis сессии удаляются по TTL, но они остаются в postgreSQL. Продумать удаление и из postgres


# Redis и работа с Java

Добавлен Redis в Python (хранение самм. контекста сервиса) и схемы запроса и ответа(JavaRequest JavaResponse)