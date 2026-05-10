# app/utils/llm_client.py
from langchain_ollama import OllamaLLM
import os

def get_llm():
    return OllamaLLM(
        model=os.getenv("OLLAMA_MODEL", "qwen3.5-driving"),
        base_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
        temperature=0.1,
        num_predict=512,
        request_timeout=120
    )

def call_llm(prompt: str) -> str:
    return get_llm().invoke(prompt)