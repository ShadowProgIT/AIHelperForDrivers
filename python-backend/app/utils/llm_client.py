# app/utils/llm_client.py
from langchain_ollama import OllamaLLM
import os

def get_llm():
    """Возвращает экземпляр LLM для работы с Ollama"""
    return OllamaLLM(
        model=os.getenv("OLLAMA_MODEL", "qwen3.5-driving"),
        base_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
        temperature=0.2,
    )

def call_llm(prompt: str) -> str:
    """Отправляет промпт в LLM и возвращает ответ"""
    llm = get_llm()
    return llm.invoke(prompt)