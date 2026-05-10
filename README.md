# Контракт. Структура JSON для обмена backend с AI 
{
    "sessionId": "session ID",
    "requestMode": "theory/practice",
    "content": "текст запроса пользователя",
    "image_url": "относительная ссылка на файл изображения"
}

# Контракт. Префикс для хранения java-сессий в Redis
backend:session

# Развёртывание модели. PowerShell, Docker. Команды
Создаёшь папки на диске. в driving-ai файл docker-compose.yml

docker compose up -d

docker exec -it ollama-server sh (зайти в оламу в ней работать)
ollama create qwen3.5-driving -f /Modelfile (уже в bash-е внутри оламы)

ollama list (проверка наличия модели qwen в ollama)

Порты:
Redis - 6379
Python - 8000