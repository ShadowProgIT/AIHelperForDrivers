# app/agents/theory_agent.py
import re
import logging
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from app.rag.vector_store import search_pdd
from app.utils.redis_client import redis_memory
from app.utils.llm_client import get_llm  # Твоя фабрика с local/global
from app.utils.safety_guard import guard_request
logger = logging.getLogger(__name__)

def clean_llm_response(text: str) -> str:
    if not text:
        return "Нет ответа от модели"
    text = re.sub(r'<?think>?.*?</?think>?', '', text, flags=re.DOTALL | re.IGNORECASE)
    match = re.search(r'[а-яА-Я]{3,}', text)
    if match:
        text = text[match.start():]
    text = text.strip()
    if not text:
        return "Модель не сгенерировала ответ на русском языке."
    return text.strip()

def generate_new_summary(old_summary: str, question: str, answer: str) -> str:
    prompt = f"""Ты ведешь краткую заметку о ходе диалога. Обнови резюме, добавив суть последнего обмена.
Старое резюме: "{old_summary or 'Диалог начался.'}"
Вопрос: "{question}"
Ответ: "{answer}"
Новое резюме (2-3 предложения, только суть):"""

    try:
        llm = get_llm()
        raw = llm.invoke(prompt)
        return clean_llm_response(raw)
    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        return old_summary

QA_PROMPT = PromptTemplate.from_template(
    """Ты — эксперт по ПДД РФ. Отвечай кратко, по делу, со ссылками на пункты. 
    Отвечай только на русском языке, а также НЕ выводи процесс размышления и теги.
Используй ТОЛЬКО предоставленный контекст из правил.

РЕЗЮМЕ ПРЕДЫДУЩЕГО ДИАЛОГА:
{context_summary}

АКТУАЛЬНЫЙ КОНТЕКСТ ИЗ ПДД:
{rag_context}

ВОПРОС ПОЛЬЗОВАТЕЛЯ:
{question}

ОТВЕТ:"""
)

def process_theory_request(
        question: str,
        session_id: str,
        provider: str = "local"
) -> dict:
    current_summary = redis_memory.get_summary(session_id) or ""
    rag_context, sources = search_pdd(question, k=5)
    llm = get_llm(provider)
    qa_chain = LLMChain(llm=llm, prompt=QA_PROMPT)
    try:
        result = qa_chain.invoke({
            "context_summary": current_summary,
            "rag_context": rag_context,
            "question": question
        })
        raw_answer = result['text']
        final_answer = clean_llm_response(raw_answer)
        new_summary = f"Q: {question[:100]}. A: {final_answer[:100]}..."
        redis_memory.save_summary(session_id, new_summary)
    except Exception as e:
        logger.error(f"QA Chain Error: {e}")
        return {"answer": "Ошибка генерации ответа.", "sources": sources}
    return {
        "answer": final_answer,
        "sources": sources
    }