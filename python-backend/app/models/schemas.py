# app/models/schemas.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, Optional


class JavaRequest(BaseModel):
    sessionId: str = Field(..., description="ID сессии")
    requestType: Literal["TEXT", "AUDIO"] = Field(..., description="Тип запроса")
    content: Optional[str] = Field(None, description="Текст вопроса (для TEXT)")
    audio_file: Optional[str] = Field(None, description="Имя файла (для AUDIO)")
    modelType: Literal["LOCAL", "GLOBAL"] = Field(default="LOCAL", description="Выбор модели")


class JavaResponse(BaseModel):
    model_config = ConfigDict(exclude_none=True)
    sessionId: str
    content: str
    audio_response: Optional[str] = None
    @classmethod
    def text_response(cls, session_id: str, answer: str) -> "JavaResponse":
        return cls(sessionId=session_id, content=answer)
    @classmethod
    def with_audio(cls, session_id: str, answer: str, filename: str) -> "JavaResponse":
        return cls(sessionId=session_id, content=answer, audio_response=filename)
    @classmethod
    def error_response(cls, session_id: str, message: str) -> "JavaResponse":
        return cls(sessionId=session_id, content=f"Ошибка: {message}")