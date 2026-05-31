# app/models/class_model.py
import os
import joblib
import logging
from pathlib import Path
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

class SafetyClassifier:

    _instance = None
    _model = None
    _vectorizer = None
    THRESHOLD = 0.65
    REDIRECT_RESPONSES = [
        "Я не могу помочь с этим запросом. Давайте обсудим безопасные темы, связанные с ПДД.",
        "Этот вопрос выходит за рамки моей компетенции. Спросите о правилах дорожного движения.",
        "Я создан для помощи в изучении ПДД. Пожалуйста, задавайте вопросы по теме вождения.",
        "Извините, но я не отвечаю на такие запросы. Чем могу помочь по правилам дорожного движения?"
    ]
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    @classmethod
    def load(cls,
             model_path: Optional[str] = None,
             vectorizer_path: Optional[str] = None) -> bool:
        if cls._model is not None:
            return True

        model_path = model_path or "app/models/safety_classifier.pkl"
        vectorizer_path = vectorizer_path or "app/models/tfidf_vectorizer.pkl"

        try:
            if not os.path.exists(model_path) or not os.path.exists(vectorizer_path):
                logger.warning("Модели не найдены. Классификатор отключён.")
                return False
            cls._model = joblib.load(model_path)
            cls._vectorizer = joblib.load(vectorizer_path)
            logger.info("SafetyClassifier загружен")
            return True
        except Exception as e:
            logger.error(f"Ошибка загрузки классификатора: {e}")
            return False

    @classmethod
    def _preprocess(cls, text: str) -> str:
        import re
        text = text.lower()
        text = re.sub(r'http\S+|www\S+|https\S+', '', text)
        text = re.sub(r'[^а-яА-ЯёЁ0-9\s.,!?;:-]', ' ', text)
        return re.sub(r'\s+', ' ', text).strip()

    @classmethod
    def check(cls, text: str) -> Tuple[bool, float, str]:
        if cls._model is None and not cls.load():
            return False, 0.0, ""
        processed = cls._preprocess(text)
        try:
            vec = cls._vectorizer.transform([processed])
            proba = cls._model.predict_proba(vec)[0]
            harmful_prob = proba[1] if len(proba) > 1 else 0.0
            if harmful_prob >= cls.THRESHOLD:
                import random
                redirect = random.choice(cls.REDIRECT_RESPONSES)
                logger.warning(f"Вредоносный запрос (conf={harmful_prob:.2f}): '{text[:100]}...'")
                return True, harmful_prob, redirect
            return False, harmful_prob, ""
        except Exception as e:
            logger.error(f"Ошибка классификации: {e}")
            return False, 0.0, ""

    @classmethod
    def get_safe_response(cls, original_question: str) -> str:
        is_harmful, conf, redirect = cls.check(original_question)
        return redirect if is_harmful else None

try:
    if not SafetyClassifier.load():
        logger.warning("SafetyClassifier не загружен — проверки безопасности отключены")
except Exception as e:
    logger.error(f"Критическая ошибка инициализации SafetyClassifier: {e}")