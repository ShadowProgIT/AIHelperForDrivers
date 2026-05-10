# app/models/response.py
from pydantic import BaseModel, Field
from typing import Optional, List, Literal


class AIResponse(BaseModel):
    """Единая модель ответа для Java-парсинга"""
    status: Literal["success", "error"]
    sessionId: str
    mode: Optional[Literal["theory", "practice"]] = None  # requestMode из запроса

    # Поля для success
    answer: Optional[str] = None
    sources: Optional[List[str]] = None  # Только для theory
    imageDescription: Optional[str] = None  # Только для practice

    # Поля для error
    message: Optional[str] = None
    code: Optional[int] = None

    #Фабричные методы для удобства

    @classmethod
    def theory_success(cls, session_id: str, answer: str, sources: List[str]) -> "AIResponse":
        return cls(
            status="success",
            sessionId=session_id,
            mode="theory",
            answer=answer,
            sources=sources
        )

    @classmethod
    def practice_success(cls, session_id: str, answer: str, image_desc: Optional[str] = None) -> "AIResponse":
        return cls(
            status="success",
            sessionId=session_id,
            mode="practice",
            answer=answer,
            imageDescription=image_desc
        )

    @classmethod
    def error(cls, session_id: str, message: str, code: int) -> "AIResponse":
        return cls(
            status="error",
            sessionId=session_id,
            mode=None,
            message=message,
            code=code
        )