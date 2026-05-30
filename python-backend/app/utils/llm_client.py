# app/utils/llm_factory.py
import logging
import os
from langchain_ollama import OllamaLLM
from langchain_gigachat.chat_models import GigaChat
from typing import Literal

logger = logging.getLogger(__name__)

def get_llm(provider: Literal["local", "global"] = "local"):
    """
    Фабрика LLM.
    provider: 'local' (Ollama) или 'gigachat' (Sber Cloud)
    """
    logger.info(f"🤖 Using LLM provider: {provider}")
    if provider == "global":
        token = os.getenv("GIGACHAT_TOKEN")
        if not token:
            raise ValueError("GIGACHAT_TOKEN not found in .env")

        return GigaChat(
            credentials=token,  # Просто передаем токен
            scope="GIGACHAT_API_PERS",  # Scope для физлиц
            model="GigaChat",  # Или "GigaChat"
            verify_ssl_certs=False,  # Важно для локальной разработки без сертификатов Сбера
            temperature=0.1
        )
    else:
        # Default: Local Ollama
        return OllamaLLM(
            model=os.getenv("OLLAMA_MODEL", "qwen3.5-driving"),
            base_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
            temperature=0.1,
            num_predict=1024
        )

