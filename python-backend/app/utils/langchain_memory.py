# app/utils/langchain_memory.py
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, messages_from_dict, messages_to_dict
from app.utils.redis_client import redis_memory
import json
from typing import List, Optional

class LangChainRedisHistory(BaseChatMessageHistory):

    def __init__(self, session_id: str, ttl_seconds: int = 86400):
        self.session_id = session_id
        self.redis_key = f"ai:history:{session_id}"
        self.summary_key = f"ai:summary:{session_id}"
        self.ttl = ttl_seconds
    @property
    def messages(self) -> List[BaseMessage]:
        try:
            raw = redis_memory.redis_client.get(self.redis_key)
            if not raw:
                return []
            data = json.loads(raw)
            return messages_from_dict(data)
        except Exception as e:
            return []

    def add_message(self, message: BaseMessage) -> None:
        try:
            messages = self.messages
            messages.append(message)
            redis_memory.redis_client.set(
                self.redis_key,
                json.dumps(messages_to_dict(messages)),
                ex=self.ttl
            )
        except Exception:
            pass

    def add_messages(self, messages: List[BaseMessage]) -> None:
        for msg in messages:
            self.add_message(msg)

    def clear(self) -> None:
        try:
            redis_memory.redis_client.delete(self.redis_key)
        except Exception:
            pass

    def get_summary(self) -> Optional[str]:
        return redis_memory.get_summary(self.session_id)

    def save_summary(self, summary: str) -> None:
        redis_memory.save_summary(self.session_id, summary)

    def get_context_for_prompt(self) -> str:
        summary = self.get_summary()
        if summary:
            return summary
        msgs = self.messages[-6:]
        if not msgs:
            return ""
        context_parts = []
        for msg in msgs:
            role = "Пользователь" if isinstance(msg, HumanMessage) else "Ассистент"
            context_parts.append(f"{role}: {msg.content}")

        return "\n".join(context_parts)