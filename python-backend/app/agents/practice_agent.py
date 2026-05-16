# app/agents/practice_agent.py
import re
import logging
from typing import Dict, Optional
from app.utils.redis_client import redis_memory
from app.utils.llm_client import get_llm
from app.rag.vector_store import search_pdd

logger = logging.getLogger(__name__)


def clean_voice_response(text: str) -> str:
    """
    Жесткая очистка текста для голосового синтеза (TTS).
    1. Удаляет теги мышления <think>...</think>.
    2. Удаляет ссылки на пункты ПДД (водителю сложно их воспринимать на слух).
    3. Оставляет только 1-2 коротких предложения.
    """
    if not text:
        return "Будьте внимательнее на дороге."

    # 1. Удаляем блоки мышления
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)

    # 2. Режем до первого русского слова (если модель начала с английского)
    match = re.search(r'[а-яА-Я]{3,}', text)
    if match:
        text = text[match.start():]

    # 3. Удаляем упоминания пунктов (п. 12.4, пункт 5 и т.д.)
    text = re.sub(r'\(?\s*[пП]ункт?\s*[\d.]+\s*\)?', '', text)
    text = re.sub(r'\(?\s*[пП]\.\s*[\d.]+\s*\)?', '', text)
    text = re.sub(r'согласно\s+пункту?\s*[\d.]+', '', text, flags=re.IGNORECASE)

    # 4. Убираем лишние пробелы
    text = ' '.join(text.strip().split())

    # 5. Берем только первое предложение (максимум 150 символов)
    sentences = [s.strip() for s in text.split('.') if s.strip()]
    if not sentences:
        return "Не могу точно определить ситуацию."

    result = sentences[0] + '.'
    if len(result) > 150:
        result = result[:147] + '...'

    return result.strip()


def is_safety_critical(situation: str) -> bool:
    """Проверка на опасные ключевые слова для мгновенной реакции"""
    keywords = ["авария", "дтп", "пешеход", "ребенок", "красный", "стоп", "тормоз", "опасно"]
    return any(k in situation.lower() for k in keywords)


def get_emergency_response(situation: str) -> str:
    """Генерация срочного предупреждения без LLM"""
    if "пешеход" in situation.lower() or "человек" in situation.lower():
        return "Внимание! Пешеход на дороге, притормозите!"
    if "красный" in situation.lower():
        return "Остановитесь! Красный сигнал светофора!"
    return "Осторожно! Снизьте скорость и будьте внимательнее."


def process_practice_request(
        question: str,
        session_id: str,
        audio_file: Optional[str] = None
) -> Dict[str, Optional[str]]:
    """
    Основная логика Practice Agent.
    Возвращает: {"answer": "...", "audio_filename": "response_xyz.wav"}
    """
    logger.info(f"🎙️ Practice Request | Session: {session_id} | File: {audio_file}")
    logger.info(f"   Text: '{question}'")

    # 1. Экстренный ответ (без LLM)
    if is_safety_critical(question):
        emergency_text = get_emergency_response(question)
        # Для экстренных случаев тоже делаем TTS
        from app.utils.salute_client import salute_client
        import os, uuid
        output_filename = f"response_{uuid.uuid4().hex[:8]}.wav"
        output_path = os.path.join("output", output_filename)  # Относительно корня проекта
        os.makedirs("output", exist_ok=True)
        try:
            salute_client.text_to_speech(emergency_text, output_path)
        except:
            output_filename = None
        return {"answer": emergency_text, "audio_filename": output_filename}

    # 2. Контекст из Redis
    try:
        context_summary = redis_memory.get_summary(session_id) or ""
    except Exception as e:
        logger.error(f"Redis Error: {e}")
        context_summary = ""

    # 3. RAG поиск
    try:
        rag_context, sources = search_pdd(question, k=3)
    except Exception as e:
        logger.error(f"RAG Error: {e}")
        rag_context = ""
        sources = []

    # 4. Промпт для голоса
    system_prompt = f"""Ты — голосовой ассистент водителя.
Отвечай ОЧЕНЬ КРАТКО (1 предложение). Начинай с действия.
Не цитируй пункты ПДД.

КОНТЕКСТ: {context_summary}
СИТУАЦИЯ: {question}

ОТВЕТ:"""

    # 5. Генерация ответа
    try:
        llm = get_llm()
        raw_answer = llm.invoke(system_prompt)
        final_answer = clean_voice_response(raw_answer)
    except Exception as e:
        logger.error(f"LLM Error: {e}")
        final_answer = "Система недоступна. Будьте внимательны."

    # 6. 🔥 СИНТЕЗ РЕЧИ (TTS) — ЭТОГО НЕ ХВАТАЛО!
    from app.utils.salute_client import salute_client
    import os, uuid

    output_filename = None
    try:
        # Генерируем имя файла
        output_filename = f"response_{uuid.uuid4().hex[:8]}.wav"
        # Путь относительно корня проекта (python-backend)
        output_path = os.path.join("output", output_filename)
        os.makedirs("output", exist_ok=True)

        # Вызываем TTS
        salute_client.text_to_speech(final_answer, output_path)
        logger.info(f"✅ TTS saved: {output_filename}")

    except Exception as e:
        logger.error(f"TTS Error: {e}")
        output_filename = None  # Если TTS упал, не возвращаем имя файла

    return {
        "answer": final_answer,
        "audio_filename": output_filename  # ← ВОЗВРАЩАЕМ ИМЯ ФАЙЛА!
    }