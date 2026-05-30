# app/main.py
from pathlib import Path

from fastapi import FastAPI, BackgroundTasks
from app.models.schemas import JavaRequest, JavaResponse
from app.agents.theory_agent import process_theory_request, generate_new_summary
from app.agents.practice_agent import process_practice_request
from app.utils.redis_client import redis_memory
from dotenv import load_dotenv
import logging, os

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Driving Assistant")

APP_ROOT = Path(__file__).resolve().parent.parent

INPUT_DIR = APP_ROOT / "audio_input"
OUTPUT_DIR = APP_ROOT / "audio_output"

logger.info(f"📂 APP_ROOT: {APP_ROOT}")
logger.info(f"📂 INPUT_DIR: {INPUT_DIR}")
logger.info(f"📂 OUTPUT_DIR: {OUTPUT_DIR}")

# Создаём папки, если нет


def update_session_summary(background_session_id: str, question: str, answer: str):
    try:
        old_summary = redis_memory.get_summary(background_session_id) or ""
        new_summary = generate_new_summary(old_summary, question, answer)
        redis_memory.save_summary(background_session_id, new_summary)
    except Exception as e:
        logger.error(f"Background summary update failed: {e}")


@app.post("/predict", response_model=JavaResponse)
async def handle_java_request(background_tasks: BackgroundTasks, request: JavaRequest):
    try:
        # === Конвертация modelType → provider ===
        # Java присылает "LOCAL"/"GLOBAL", наш код ожидает "local"/"global"
        provider = "global" if request.modelType == "GLOBAL" else "local"

        # --- TEXT MODE ---
        if request.requestType == "TEXT":
            if not request.content:
                return JavaResponse.error_response(request.sessionId, "Missing content for TEXT mode")

            # Передаём provider в агент для выбора модели
            result = process_theory_request(
                question=request.content,
                session_id=request.sessionId,
                provider=provider  # <-- ПЕРЕДАЁМ ВЫБРАННУЮ МОДЕЛЬ
            )

            background_tasks.add_task(
                update_session_summary,
                request.sessionId,
                request.content,
                result["answer"]
            )

            return JavaResponse.text_response(
                session_id=request.sessionId,
                answer=result["answer"]
            )

        # --- AUDIO MODE ---
        elif request.requestType == "AUDIO":
            if not request.audio_file:
                return JavaResponse.error_response(request.sessionId, "Missing audio_file for AUDIO mode")

            input_path = os.path.join(INPUT_DIR, request.audio_file)

            # === ФИКС: Если файл не найден, пробуем добавить .wav ===
            if not os.path.exists(input_path):
                # Пробуем с расширением .wav
                input_path_with_ext = input_path if input_path.endswith('.wav') else f"{input_path}.wav"
                if os.path.exists(input_path_with_ext):
                    input_path = input_path_with_ext
                    logger.info(f"✅ Файл найден с добавлением .wav: {input_path}")
                else:
                    logger.error(f"❌ Файл не найден: {input_path} (и с .wav тоже)")
                    return JavaResponse.error_response(request.sessionId, f"File not found: {request.audio_file}")
            logger.info(f"🔍 Проверяю файл: {input_path}")

            # 1. STT (распознавание речи) — ОДИН ВЫЗОВ, с логированием
            try:
                from app.utils.salute_client import salute_client
                logger.info("🎤 Запускаю STT...")
                recognized_text = salute_client.speech_to_text(input_path)
                logger.info(f"✅ STT результат: '{recognized_text}'")

                if not recognized_text or len(recognized_text.strip()) < 3:
                    logger.warning("⚠️ STT вернул пустой или слишком короткий текст")
                    return JavaResponse.error_response(request.sessionId, "Speech recognition failed")
            except Exception as e:
                logger.error(f"❌ STT Error: {e}", exc_info=True)
                return JavaResponse.error_response(request.sessionId, f"STT Error: {str(e)}")

            # 2. Agent + TTS
            logger.info(f"🤖 Запускаю Practice Agent с вопросом: '{recognized_text[:50]}...'")
            agent_result = process_practice_request(
                question=recognized_text,
                session_id=request.sessionId,
                provider=provider,
                output_dir=OUTPUT_DIR
            )
            logger.info(f"✅ Agent результат: {agent_result}")

            background_tasks.add_task(
                update_session_summary,
                request.sessionId,
                recognized_text,
                agent_result["answer"]
            )

            if agent_result.get("audio_filename"):
                logger.info(f"🔊 TTS файл создан: {agent_result['audio_filename']}")
                return JavaResponse.with_audio(
                    session_id=request.sessionId,
                    answer=agent_result["answer"],
                    filename=agent_result["audio_filename"]
                )
            else:
                logger.error("❌ TTS не создал файл")
                return JavaResponse.error_response(request.sessionId, "TTS generation failed")

        else:
            return JavaResponse.error_response(request.sessionId, f"Unknown type: {request.requestType}")

    except Exception as e:
        logger.error(f"Global Error: {e}", exc_info=True)
        return JavaResponse.error_response(session_id=request.sessionId, message=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy"}