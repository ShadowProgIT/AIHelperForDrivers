# app/utils/safety_guard.py
from app.models.class_model import SafetyClassifier
import logging
from typing import TypedDict

logger = logging.getLogger(__name__)



class SafetyResult(TypedDict):
    blocked: bool
    response: str
    confidence: float

def guard_request(text: str) -> SafetyResult:
    """Универсальная проверка запроса."""
    is_harmful, confidence, redirect_msg = SafetyClassifier.check(text)
    return {
        "blocked": is_harmful,
        "response": redirect_msg if is_harmful else "",
        "confidence": confidence
    }