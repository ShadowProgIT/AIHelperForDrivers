# app/models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, Literal


class JavaRequest(BaseModel):
    sessionId: str = Field(..., description="ID сессии от Java")
    content: str = Field(..., description="Текст вопроса")
    mode: Literal["THEORY", "PRACTICE"] = Field(..., description="Режим")
    image_url: Optional[str] = Field(None, description="URL изображения")


class JavaResponse(BaseModel):
    sessionId: str
    requestMode: Literal["THEORY", "PRACTICE"]
    content: str
    image_url: Optional[str] = None

    @classmethod
    def theory(cls, session_id: str, answer: str) -> "JavaResponse":
        return cls(sessionId=session_id, requestMode="THEORY", content=answer)

    @classmethod
    def practice(cls, session_id: str, answer: str, image_desc: Optional[str] = None) -> "JavaResponse":
        return cls(sessionId=session_id, requestMode="PRACTICE", content=answer, image_url=image_desc)

    @classmethod
    def error(cls, session_id: str, mode: str, message: str) -> "JavaResponse":
        return cls(sessionId=session_id, requestMode=mode, content=f"Ошибка: {message}")