# app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal
from app.models.response import AIResponse
from app.agents.theory_agent import process_theory_request

# from app.agents.practice_agent import process_practice_request  # позже

app = FastAPI(title="AI Driving Assistant")


class AIRequest(BaseModel):
    sessionId: str
    requestMode: Literal["theory", "practice"]
    content: str
    image_url: Optional[str] = None


@app.post("/api/ai-process", response_model=AIResponse)
async def handle_ai_request(request: AIRequest):
    try:
        if request.requestMode == "theory":
            result = process_theory_request(request.content, request.sessionId)
            return AIResponse.theory_success(
                session_id=request.sessionId,
                answer=result["answer"],
                sources=result.get("sources", [])
            )

        elif request.requestMode == "practice":
            # Заглушка для практики
            return AIResponse.practice_success(
                session_id=request.sessionId,
                answer="Практический режим в разработке",
                image_desc=None
            )

        else:
            raise HTTPException(status_code=400, detail="Invalid requestMode")

    except Exception as e:
        return AIResponse.error(
            session_id=request.sessionId,
            message=str(e),
            code=500
        )