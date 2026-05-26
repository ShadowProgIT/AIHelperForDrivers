# app/agents/theory_agent.py
import re
import logging
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from app.rag.vector_store import search_pdd
from app.utils.redis_client import redis_memory
from app.utils.llm_client import get_llm  # Твоя фабрика с local/global

logger = logging.getLogger(__name__)


def clean_llm_response(text: str) -> str:
    """
    Жёстко очищает ответ модели (СТАРАЯ РАБОЧАЯ ВЕРСИЯ):
    1. Удаляет блоки <think> ... </think>
    2. Удаляет любые английские рассуждения до первого русского предложения
    3. Возвращает только чистый ответ
    """
    if not text:
        return "Нет ответа от модели"

    # 1. Удаляем теги мышления
    text = re.sub(r'<?think>?.*?</?think>?', '', text, flags=re.DOTALL | re.IGNORECASE)

    # 2. Обрезаем до первого русского слова (защита от английского преамбула)
    match = re.search(r'[а-яА-Я]{3,}', text)
    if match:
        text = text[match.start():]

    # 3. Убираем лишние переносы строк
    text = text.strip()

    # 4. Если пусто после чистки
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
        return old_summary


# === ЦЕПОЧКА 1: QA CHAIN (для TEXT режима) ===
# Используем PromptTemplate + LLMChain для явного соответствия требованию "2 цепочки LangChain"
QA_PROMPT = PromptTemplate.from_template(
    """Ты — эксперт по ПДД РФ. Отвечай кратко, по делу, со ссылками на пункты. 
    Отвечай только на русском языке, а также НЕ выводи процесс размышления и теги.
Используй ТОЛЬКО предоставленный контекст из правил.

РЕЗЮМЕ ПРЕДЫДУЩЕГО ДИАЛОГА:
{context_summary}

АКТУАЛЬНЫЙ КОНТЕКСТ ИЗ ПДД:
{rag_context}

ВОПРОС:
{question}

ОТВЕТ:"""
)


def process_theory_request(
        question: str,
        session_id: str,
        provider: str = "local"  # <-- НОВЫЙ ПАРАМЕТР для переключения моделей
) -> dict:
    """
    Основная логика Theory Agent.

    Реализует требование: "Использование 2-х цепочек LangChain".
    Цепочка 1 (здесь): QA_PROMPT | LLMChain для генерации ответа.
    """

    # 1. Загружаем текущее саммари из Redis
    current_summary = redis_memory.get_summary(session_id) or ""

    # 2. RAG-поиск по текущему вопросу
    rag_context, sources = search_pdd(question, k=5)

    # 3. Инициализация LLM через фабрику (поддержка local/global)
    llm = get_llm(provider)

    # 4. Создаем и запускаем ЦЕПОЧКУ 1 (QA Chain) — явное использование LangChain
    qa_chain = LLMChain(llm=llm, prompt=QA_PROMPT)

    try:
        # invoke возвращает dict {'text': '...'}
        result = qa_chain.invoke({
            "context_summary": current_summary,
            "rag_context": rag_context,
            "question": question
        })
        raw_answer = result['text']
        final_answer = clean_llm_response(raw_answer)

        # 5. Обновление контекста в Redis (внутри логики обработки)
        new_summary = f"Q: {question[:100]}. A: {final_answer[:100]}..."
        redis_memory.save_summary(session_id, new_summary)

    except Exception as e:
        logger.error(f"QA Chain Error: {e}")
        return {"answer": "Ошибка генерации ответа.", "sources": sources}

    return {
        "answer": final_answer,
        "sources": sources
    }