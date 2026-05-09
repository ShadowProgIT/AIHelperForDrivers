# app/main.py
from fastapi import FastAPI
from app.utils.llm_client import call_llm

app = FastAPI(
    title="AI Driving Assistant",
    description="Помощник для обучения вождению с использованием AI",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"status": "ok", "service": "python-backend"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "llm": "connected"}

@app.post("/api/test")
def test_llm(prompt: str = "Привет! Кто ты?"):
    """Тестовый эндпоинт для проверки связи с LLM"""
    answer = call_llm(prompt)
    return {"prompt": prompt, "answer": answer}