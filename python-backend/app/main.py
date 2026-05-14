# app/main.py
from fastapi import FastAPI, BackgroundTasks
from app.models.schemas import JavaRequest, JavaResponse
from app.agents.theory_agent import process_theory_request, generate_new_summary
from app.utils.redis_client import redis_memory
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI Driving Assistant")


# Фоновая задача: обновляет саммари ПОСЛЕ того, как ответ уже ушел клиенту
def update_session_summary(background_session_id: str, question: str, answer: str):
    try:
        old_summary = redis_memory.get_summary(background_session_id) or ""
        new_summary = generate_new_summary(old_summary, question, answer)
        redis_memory.save_summary(background_session_id, new_summary)
    except Exception as e:
        # Не ломаем основной поток, просто логируем
        print(f"️ Background summary update failed: {e}")


@app.post("/predict", response_model=JavaResponse)
async def handle_java_request(
        background_tasks: BackgroundTasks,
        request: JavaRequest
):
    try:
        if request.mode == "THEORY":
            result = process_theory_request(request.content, request.sessionId)

            # Добавляем задачу в фон: Redis обновится асинхронно
            background_tasks.add_task(
                update_session_summary,
                request.sessionId,
                request.content,
                result["answer"]
            )

            return JavaResponse.theory(
                session_id=request.sessionId,
                answer=result["answer"]
            )

        elif request.mode == "PRACTICE":
            # Заглушка для практики
            return JavaResponse.practice(
                session_id=request.sessionId,
                answer="Практический режим в разработке",
                image_desc=None
            )

        else:
            return JavaResponse.error(
                session_id=request.sessionId,
                mode=request.mode,
                message="Unknown mode"
            )

    except Exception as e:
        return JavaResponse.error(
            session_id=request.sessionId,
            mode=request.mode,
            message=str(e)
        )


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "redis": "connected" if redis_memory.ping() else "disconnected",
        "service": "python-ai-backend"
    }