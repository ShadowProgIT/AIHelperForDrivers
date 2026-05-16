# app/models/schemas.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, Optional

class JavaRequest(BaseModel):
    sessionId: str = Field(..., description="ID сессии")
    requestType: Literal["TEXT", "AUDIO"] = Field(..., description="Тип запроса")
    content: Optional[str] = Field(None, description="Текст вопроса (для TEXT)")
    audio_file: Optional[str] = Field(None, description="Имя файла (для AUDIO)")

class JavaResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    sessionId: str
    requestType: Literal["TEXT", "AUDIO", "ERROR"]
    content: str
    audio_response: Optional[str] = None

    @classmethod
    def make_text_response(cls, session_id: str, answer: str) -> "JavaResponse":
        return cls(sessionId=session_id, requestType="TEXT", content=answer)

    @classmethod
    def make_audio_response(cls, session_id: str, answer: str, filename: str) -> "JavaResponse":
        return cls(sessionId=session_id, requestType="AUDIO", content=answer, audio_response=filename)

    @classmethod
    def make_error_response(cls, session_id: str, message: str) -> "JavaResponse":
        return cls(sessionId=session_id, requestType="ERROR", content=message)