# app/main.py
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

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_DIR = os.path.join(PROJECT_ROOT, "audio_input")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "audio_output")


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
        if request.requestType == "TEXT":
            if not request.content:
                return JavaResponse.make_error_response(request.sessionId, "Missing content for TEXT mode")

            result = process_theory_request(request.content, request.sessionId)
            background_tasks.add_task(update_session_summary, request.sessionId, request.content, result["answer"])
            return JavaResponse.make_text_response(session_id=request.sessionId, answer=result["answer"])

        elif request.requestType == "AUDIO":
            if not request.audio_file:
                return JavaResponse.make_error_response(request.sessionId, "Missing audio_file for AUDIO mode")

            input_path = os.path.join(INPUT_DIR, request.audio_file)
            if not os.path.exists(input_path):
                return JavaResponse.make_error_response(request.sessionId, f"File not found: {request.audio_file}")

            # 1. STT
            try:
                from app.utils.salute_client import salute_client
                recognized_text = salute_client.speech_to_text(input_path)
                if not recognized_text:
                    return JavaResponse.make_error_response(request.sessionId, "Speech recognition failed")
            except Exception as e:
                logger.error(f"STT Error: {e}")
                return JavaResponse.make_error_response(request.sessionId, f"STT Error: {str(e)}")

            # 2. Agent + TTS (✅ ИСПРАВЛЕНО: передача output_dir и убрана лишняя переменная)
            agent_result = process_practice_request(
                question=recognized_text,
                session_id=request.sessionId,
                output_dir=OUTPUT_DIR  # ✅ Теперь файлы падают в audio_output/
            )

            background_tasks.add_task(update_session_summary, request.sessionId, recognized_text,
                                      agent_result["answer"])

            if agent_result["audio_filename"]:
                return JavaResponse.make_audio_response(
                    session_id=request.sessionId,
                    answer=agent_result["answer"],
                    filename=agent_result["audio_filename"]
                )
            else:
                return JavaResponse.make_error_response(request.sessionId, "TTS generation failed")

        else:
            return JavaResponse.make_error_response(request.sessionId, f"Unknown type: {request.requestType}")

    except Exception as e:
        logger.error(f"Global Error: {e}")
        return JavaResponse.make_error_response(session_id=request.sessionId, message=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy"}