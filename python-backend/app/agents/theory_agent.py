# app/agents/theory_agent.py
import re
from app.rag.vector_store import search_pdd
from app.utils.redis_client import redis_memory
from app.utils.llm_client import get_llm
import logging

logger = logging.getLogger(__name__)

def clean_llm_response(text: str) -> str:
    """
    Жёстко очищает ответ модели:
    1. Удаляет блоки <think> ... </think>
    2. Удаляет любые английские рассуждения до первого русского предложения
    3. Возвращает только чистый ответ
    """
    if not text:
        return "Нет ответа от модели"

    # 1. Удаляем теги мышления (стандартный способ)
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)

    # 2. Если остались английские буквы в начале (модель не закрыла тег), режем до первого русского
    #
    match = re.search(r'[а-яА-Я]{3,}', text)
    if match:
        # Возвращаем всё начиная с этого русского слова
        text = text[match.start():]

    # 3. Убираем лишние переносы строк в начале и конце
    text = text.strip()

    # 4. Если текст пустой после чистки
    if not text:
        return "Модель не сгенерировала ответ на русском языке."

    return text.strip()


def generate_new_summary(old_summary: str, question: str, answer: str) -> str:
    """Генерирует обновленное краткое резюме диалога"""
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
        return old_summary  # Fallback: сохраняем старое


def process_theory_request(question: str, session_id: str) -> dict:
    """Основная логика Theory Agent"""
    # 1. Загружаем текущее саммари из Redis
    current_summary = redis_memory.get_summary(session_id) or ""

    # 2. RAG-поиск по текущему вопросу
    rag_context, sources = search_pdd(question, k=5)

    # 3. Формируем промпт
    system_prompt = f"""Ты — эксперт по ПДД РФ. Отвечай кратко, по делу, со ссылками на пункты.
Используй ТОЛЬКО предоставленный контекст из правил.

РЕЗЮМЕ ПРЕДЫДУЩЕГО ДИАЛОГА:
{current_summary}

АКТУАЛЬНЫЙ КОНТЕКСТ ИЗ ПДД:
{rag_context}

ВОПРОС:
{question}

ОТВЕТ:"""

    # 4. Генерация ответа
    try:
        llm = get_llm()
        raw_answer = llm.invoke(system_prompt)
        final_answer = clean_llm_response(raw_answer)
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        return {"answer": "Ошибка генерации ответа.", "sources": sources}

    return {
        "answer": final_answer,
        "sources": sources
    }