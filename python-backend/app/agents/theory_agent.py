# app/agents/theory_agent.py
import re
from app.rag.vector_store import search_pdd
from app.utils.llm_client import get_llm


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

    return text


def process_theory_request(question: str, session_id: str):
    """
    Обрабатывает вопрос по ПДД.
    """
    print(f"🔍 Поиск ответа на вопрос: {question}")

    # 1. Поиск контекста (увеличиваем k до 5 для лучшего охвата)
    try:
        context, sources = search_pdd(question, k=5)
        print(f"✅ Найдено источников: {len(sources)}")
        # Для отладки можно раскомментировать:
        # print(f"📄 Контекст: {context[:200]}...")
    except Exception as e:
        print(f"❌ Ошибка RAG: {e}")
        return {
            "answer": "Ошибка при поиске в базе ПДД.",
            "sources": []
        }

    # 2. Формируем ЖЁСТКИЙ промпт
    # Мы явно запрещаем английский и требуем краткости
    system_prompt = """Ты — эксперт по ПДД РФ. Твоя задача — отвечать на вопросы СТРОГО на основе предоставленного текста.

ПРАВИЛА ОТВЕТА:
1. ЯЗЫК: Отвечай ТОЛЬКО на русском языке. Никакого английского.
2. КОНТЕКСТ: Используй ТОЛЬКО предоставленный ниже текст. Если ответа нет, так и напиши: "В предоставленных документах нет информации".
3. ССЫЛКИ: Обязательно указывай пункты ПДД (например, "Согласно п. 10.1..."), если они есть в тексте.
4. ФОРМАТ: Отвечай кратко, по делу. Без вступлений типа "Конечно, вот ответ".
5. ЗАПРЕТ: НЕ выводи свои мысли, рассуждения или теги <think>. Сразу пиши ответ.

--- ТЕКСТ ИЗ ПДД ---
{context}
---------------------

ВОПРОС: {question}

ОТВЕТ (на русском):"""

    final_prompt = system_prompt.format(context=context, question=question)

    # 3. Вызов модели
    try:
        llm = get_llm()
        # Уменьшаем num_predict, чтобы не генерировала лишнего (если поддерживается)
        # В LangChain это можно передать через model_kwargs, но пока оставим дефолт
        raw_response = llm.invoke(final_prompt)

        print(f"📝 Сырой ответ (длина {len(raw_response)}): {raw_response[:100]}...")

        # 4. Чистка
        clean_answer = clean_llm_response(raw_response)

        print(f"✅ Чистый ответ: {clean_answer}")

    except Exception as e:
        print(f"❌ Ошибка LLM: {e}")
        return {
            "answer": f"Ошибка генерации: {str(e)}",
            "sources": sources
        }

    return {
        "answer": clean_answer,
        "sources": sources
    }