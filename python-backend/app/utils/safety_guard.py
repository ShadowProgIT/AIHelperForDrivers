# app/utils/safety_guard.py
from app.models.class_model import SafetyClassifier
import logging

logger = logging.getLogger(__name__)


def guard_request(text: str) -> dict:
    """
    Универсальная проверка запроса.

    Returns:
        {
            "blocked": bool,      # нужно ли блокировать
            "response": str,      # ответ пользователю (если блокировано)
            "confidence": float   # уверенность модели
        }
    """
    is_harmful, confidence, redirect_msg = SafetyClassifier.check(text)

    return {
        "blocked": is_harmful,
        "response": redirect_msg if is_harmful else "",
        "confidence": confidence
    }