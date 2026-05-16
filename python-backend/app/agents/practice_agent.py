# app/agents/practice_agent.py
import re
import os
import uuid
import logging
from typing import Dict, Optional
from app.utils.redis_client import redis_memory
from app.utils.llm_client import get_llm
from app.rag.vector_store import search_pdd
from app.utils.salute_client import salute_client

logger = logging.getLogger(__name__)


def clean_voice_response(text: str) -> str:
    if not text:
        return "Будьте внимательнее на дороге."

    # 1. Удаляем блоки мышления
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # 2. Обрезаем до первого русского слова (защита от английского преамбула)
    match = re.search(r'[а-яА-Я]{3,}', text)
    if match:
        text = text[match.start():]
    # 3. Удаляем ссылки на пункты ПДД
    text = re.sub(r'\(?\s*[пП]ункт?\s*[\d.]+\s*\)?', '', text)
    text = re.sub(r'\(?\s*[пП]\.\s*[\d.]+\s*\)?', '', text)
    text = re.sub(r'согласно\s+пункту?\s*[\d.]+', '', text, flags=re.IGNORECASE)

    text = ' '.join(text.strip().split())
    # 4. Берём первое предложение (макс 150 символов)
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    if not sentences:
        return "Не могу точно определить ситуацию."

    result = sentences[0] + '.'
    return result[:147] + '...' if len(result) > 150 else result.strip()


def is_safety_critical(situation: str) -> bool:
    keywords = ["авария", "дтп", "пешеход", "ребенок", "красный", "стоп", "тормоз", "опасно", "наезд"]
    return any(k in situation.lower() for k in keywords)


def get_emergency_response(situation: str) -> str:
    if "пешеход" in situation.lower() or "человек" in situation.lower():
        return "Внимание! Пешеход на дороге, притормозите!"
    if "красный" in situation.lower():
        return "Остановитесь! Красный сигнал светофора!"
    return "Осторожно! Снизьте скорость и будьте внимательнее."


def _generate_audio(text: str, output_dir: str) -> Optional[str]:
    """Внутренний хелпер для TTS"""
    filename = f"response_{uuid.uuid4().hex[:8]}.wav"
    path = os.path.join(output_dir, filename)
    os.makedirs(output_dir, exist_ok=True)
    try:
        salute_client.text_to_speech(text, path)
        return filename
    except Exception as e:
        logger.error(f"TTS Error: {e}")
        return None


def process_practice_request(
        question: str,
        session_id: str,
        output_dir: str = "output"
) -> Dict[str, Optional[str]]:
    logger.info(f"🎙️ Practice Request | Session: {session_id} | Q: '{question[:50]}...'")

    # 1. Экстренный ответ (без LLM)
    if is_safety_critical(question):
        emergency_text = get_emergency_response(question)
        audio_filename = _generate_audio(emergency_text, output_dir)
        return {"answer": emergency_text, "audio_filename": audio_filename}

    # 2. Контекст из Redis
    context_summary = ""
    try:
        context_summary = redis_memory.get_summary(session_id) or ""
    except Exception as e:
        logger.error(f"Redis Error: {e}")

    # 3. RAG поиск
    rag_context = ""
    try:
        rag_context, _ = search_pdd(question, k=3)
    except Exception as e:
        logger.error(f"RAG Error: {e}")

    # 4. Промпт для голоса (✅ ИСПРАВЛЕНО: добавлен rag_context)
    system_prompt = f"""Ты — голосовой ассистент водителя.
Отвечай ОЧЕНЬ КРАТКО (1 короткое предложение). Начинай с действия.
Не цитируй пункты ПДД вслух.
КОНТЕКСТ ДИАЛОГА: {context_summary}
ИНФОРМАЦИЯ ИЗ ПДД: {rag_context}
СИТУАЦИЯ: {question}
ОТВЕТ:"""

    # 5. Генерация ответа
    final_answer = "Система недоступна. Будьте внимательны."
    try:
        llm = get_llm()
        raw_answer = llm.invoke(system_prompt)
        final_answer = clean_voice_response(raw_answer)
    except Exception as e:
        logger.error(f"LLM Error: {e}")

    # 6. 🔥 СИНТЕЗ РЕЧИ (TTS)
    audio_filename = _generate_audio(final_answer, output_dir)

    return {"answer": final_answer, "audio_filename": audio_filename}