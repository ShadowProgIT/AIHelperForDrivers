# app/utils/redis_client.py
import os
import redis
from typing import Optional
from dotenv import load_dotenv
import logging
load_dotenv()
logger = logging.getLogger(__name__)

class RedisSessionMemory:
    def __init__(self):
        self.redis = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD") or None,
            db=int(os.getenv("REDIS_DB", "0")),
            decode_responses=True,
            socket_connect_timeout=5,
            retry_on_timeout=True
        )
        self.prefix = "ai:summary:"
        self.ttl_seconds = int(os.getenv("REDIS_SUMMARY_TTL", "86400"))

    def _get_key(self, session_id: str) -> str:
        return f"{self.prefix}{session_id}"

    def get_summary(self, session_id: str) -> Optional[str]:
        try:
            return self.redis.get(self._get_key(session_id))
        except redis.RedisError as e:
            logger.error(f"Redis GET error for {session_id}: {e}")
            return None

    def save_summary(self, session_id: str, summary: str) -> bool:
        try:
            return self.redis.setex(
                self._get_key(session_id),
                self.ttl_seconds,
                summary
            )
        except redis.RedisError as e:
            logger.error(f"Redis SET error for {session_id}: {e}")
            return False
    def delete_session(self, session_id: str) -> bool:
        try:
            return bool(self.redis.delete(self._get_key(session_id)))
        except redis.RedisError as e:
            logger.error(f"Redis DELETE error for {session_id}: {e}")
            return False

    def ping(self) -> bool:
        try:
            return self.redis.ping()
        except redis.RedisError:
            return False
redis_memory = RedisSessionMemory()