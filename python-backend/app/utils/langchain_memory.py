# app/utils/langchain_memory.py
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, messages_from_dict, messages_to_dict
from app.utils.redis_client import redis_memory
import json
from typing import List, Optional


class LangChainRedisHistory(BaseChatMessageHistory):
    """
    LangChain-совместимая история сообщений на базе Redis.
    Использует существующую инфраструктуру redis_client.py.

    Для курсовой: это реализация требования "контекстное окно через LangChain + Redis".
    """

    def __init__(self, session_id: str, ttl_seconds: int = 86400):
        """
        Args:
            session_id: ID сессии (как в твоем коде)
            ttl_seconds: Время жизни истории в Redis (по умолчанию 24 часа)
        """
        self.session_id = session_id
        self.redis_key = f"ai:history:{session_id}"  # Отдельный ключ для полной истории
        self.summary_key = f"ai:summary:{session_id}"  # Твой существующий ключ для саммари
        self.ttl = ttl_seconds

    @property
    def messages(self) -> List[BaseMessage]:
        """Получить все сообщения из Redis"""
        try:
            raw = redis_memory.redis_client.get(self.redis_key)
            if not raw:
                return []
            data = json.loads(raw)
            return messages_from_dict(data)
        except Exception as e:
            # Если не получилось распарсить — вернём пустой список (безопасный фоллбэк)
            return []

    def add_message(self, message: BaseMessage) -> None:
        """Добавить одно сообщение в историю"""
        try:
            messages = self.messages
            messages.append(message)
            redis_memory.redis_client.set(
                self.redis_key,
                json.dumps(messages_to_dict(messages)),
                ex=self.ttl
            )
        except Exception:
            pass  # Не критично, если не сохранилось

    def add_messages(self, messages: List[BaseMessage]) -> None:
        """Добавить несколько сообщений"""
        for msg in messages:
            self.add_message(msg)

    def clear(self) -> None:
        """Очистить историю сессии"""
        try:
            redis_memory.redis_client.delete(self.redis_key)
        except Exception:
            pass

    # === Методы для работы с саммари (твоя текущая логика) ===

    def get_summary(self) -> Optional[str]:
        """Получить текущее саммари (твой существующий метод)"""
        return redis_memory.get_summary(self.session_id)

    def save_summary(self, summary: str) -> None:
        """Сохранить саммари (твой существующий метод)"""
        redis_memory.save_summary(self.session_id, summary)

    def get_context_for_prompt(self) -> str:
        """
        Возвращает контекст для промпта:
        - Если есть саммари — использует его (твоя текущая логика)
        - Если нет — берёт последние 3 сообщения из истории (LangChain-фоллбэк)
        """
        summary = self.get_summary()
        if summary:
            return summary

        # Фоллбэк: последние сообщения, если саммари ещё нет
        msgs = self.messages[-6:]  # Последние 3 пары вопрос-ответ
        if not msgs:
            return ""

        context_parts = []
        for msg in msgs:
            role = "Пользователь" if isinstance(msg, HumanMessage) else "Ассистент"
            context_parts.append(f"{role}: {msg.content}")

        return "\n".join(context_parts)