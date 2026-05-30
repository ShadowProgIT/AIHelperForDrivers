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
    Умная очистка: сохраняет начало ответа, если оно осмысленное.
    """
    if not text:
        return "Будьте внимательнее на дороге."

    # 1. Удаляем блоки <think> и любые теги
    text = re.sub(r'<?think>?.*?</?think>?', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)

    # 2. Удаляем служебные маркеры
    text = re.sub(r'(Thinking Process|Analysis|Answer|Response|Conclusion|Style|Constraint):', '', text,
                  flags=re.IGNORECASE)

    # 3. Чистим лишние пробелы и переносы
    text = ' '.join(text.strip().split())

    # 4. Ищем начало русского текста (первое слово с русской буквы)
    match = re.search(r'[а-яА-Я][а-яА-Я,\s\-!?\.«»]+', text)
    if not match:
        return "Не могу дать точный ответ."

    # Берём текст начиная с этого места
    text = text[match.start():]

    # 5. Если текст уже хороший (начинается с нормального слова, длина > 30) — возвращаем как есть
    first_word = text.split()[0] if text.split() else ""
    if len(first_word) >= 2 and len(text) > 30 and not first_word.upper() == first_word:
        # Обрезаем до первой точки, но не короче 50 символов
        if '.' in text:
            sentences = text.split('.')
            candidate = sentences[0].strip() + '.'
            if len(candidate) >= 40:
                return candidate[:200]
        return text[:200].strip()

    # 6. Фоллбэк: ищем первое полноценное предложение (но игнорируем аббревиатуры типа ПДД)
    # Регулярка: слово из 2+ букв, потом текст, потом точка
    sentences = re.findall(r'([А-Яа-я]{2,}[\sа-яА-Я,\-!?«»]+[.!?])', text)
    for sentence in sentences:
        sentence = sentence.strip()
        # Пропускаем слишком короткие или подозрительные
        if len(sentence) > 25 and not sentence.upper() == sentence:
            return sentence[:200]

    # 7. Последний фоллбэк: просто берём первые 150 символов
    return text[:150].strip() + '...' if len(text) > 150 else text.strip()


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
    """Ты — эксперт по ПДД РФ, помогаешь водителям.
Твоя задача — дать понятный, полезный ответ на вопрос о правилах дорожного движения.

ПРАВИЛА ОТВЕТА:
1. Отвечай 1-2 предложениями (достаточно для голосового ответа)
2. Указывай конкретный пункт ПДД, если знаешь
3. Объясняй кратко, ПОЧЕМУ нельзя/можно
4. Если не знаешь точный пункт — дай общий совет по безопасности

ПРИМЕРЫ ХОРОШИХ ОТВЕТОВ:
❌ Слишком коротко: "Нельзя."
✅ Хорошо: "Обгон на перекрёстке запрещён согласно пункту 11.4 ПДД РФ, так как это создаёт аварийную ситуацию."

❌ Слишком коротко: "Запрещено ПДД."
✅ Хорошо: "Остановка на пешеходном переходе запрещена пунктом 12.4 ПДД. Это опасно для пешеходов."
Вопрос: {question}
Контекст ПДД: {rag_context}

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