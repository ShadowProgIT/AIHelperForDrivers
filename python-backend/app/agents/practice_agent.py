# app/agents/practice_agent.py
import re
import os
import uuid
import logging
from typing import Dict, Optional
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from app.utils.redis_client import redis_memory
from app.utils.llm_client import get_llm
from app.rag.vector_store import search_pdd
from app.utils.salute_client import salute_client

logger = logging.getLogger(__name__)


def clean_voice_response(text: str) -> str:
    """
    Простая очистка: убираем мусор и возвращаем текст.
    """
    if not text:
        return "Будьте внимательнее на дороге."

    # 1. Удаляем блоки <think>
    text = re.sub(r'<?think>?.*?</?think>?', '', text, flags=re.DOTALL | re.IGNORECASE)

    # 2. Удаляем любые теги <...>
    text = re.sub(r'<[^>]+>', '', text)

    # 3. Просто чистим пробелы и переносы
    text = ' '.join(text.strip().split())

    # 4. Если текст есть — возвращаем, обрезая если слишком длинный
    if text:
        return text[:250]  # 250 символов ~ 15-20 секунд речи

    return "Не могу дать точный ответ."


def is_safety_critical(situation: str) -> bool:
    keywords = ["авария", "дтп", "ребенок", "стоп", "тормоз", "опасно", "наезд"]
    return any(k in situation.lower() for k in keywords)


def get_emergency_response(situation: str) -> str:
    if "красный" in situation.lower():
        return "Остановитесь! Красный сигнал светофора!"
    return "Осторожно! Снизьте скорость и будьте внимательнее."


def _generate_audio(text: str, output_dir: str) -> Optional[str]:
    filename = f"response_{uuid.uuid4().hex[:8]}.wav"
    path = os.path.join(output_dir, filename)
    os.makedirs(output_dir, exist_ok=True)
    try:
        salute_client.text_to_speech(text, path)
        return filename
    except Exception as e:
        logger.error(f"TTS Error: {e}")
        return None


VOICE_PROMPT = PromptTemplate.from_template(
    """Ты — голосовой ассистент водителя. Отвечай кратко (2-3 предложения) по ПДД РФ.
Не повторяй вопрос. Не пиши "Ситуация:". Сразу давай ответ.

Контекст ПДД: {rag_context}

Запрос водителя: {question}

Ответ:"""
)


def process_practice_request(
        question: str,
        session_id: str,
        provider: str = "local",
        output_dir: str = "audio_output"
) -> Dict[str, Optional[str]]:
    logger.info(f"🎙️ Practice Request | Session: {session_id} | Q: '{question[:50]}...'")

    # 1. Экстренный ответ
    if is_safety_critical(question):
        emergency_text = get_emergency_response(question)
        audio_filename = _generate_audio(emergency_text, output_dir)
        return {"answer": emergency_text, "audio_filename": audio_filename}

    # 2. Контекст и RAG
    context_summary = redis_memory.get_summary(session_id) or ""
    rag_context, _ = search_pdd(question, k=3)

    # Если контекст пустой — пишем явно
    if not rag_context or len(rag_context.strip()) < 20:
        rag_context = "Контекст не найден. Используй общие знания ПДД."

    # 3. LLM Chain
    try:
        llm = get_llm(provider)
        voice_chain = LLMChain(llm=llm, prompt=VOICE_PROMPT)

        # ВАЖНО: передаём ТОЧНО те же ключи, что в промпте {question} и {rag_context}
        result = voice_chain.invoke({
            "question": question,
            "rag_context": rag_context
        })

        raw_answer = result['text']
        logger.info(f"RAW ANSWER: {raw_answer[:100]}")  # Для отладки

        final_answer = clean_voice_response(raw_answer)

        # Обновление Redis
        new_summary = f"Voice Q: {question[:100]}. A: {final_answer}"
        redis_memory.save_summary(session_id, new_summary)

    except Exception as e:
        logger.error(f"Voice Chain Error: {e}", exc_info=True)
        final_answer = "Система недоступна."

    # 4. TTS
    audio_filename = _generate_audio(final_answer, output_dir)
    return {"answer": final_answer, "audio_filename": audio_filename}