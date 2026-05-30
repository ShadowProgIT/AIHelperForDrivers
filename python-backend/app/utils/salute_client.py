# app/utils/salute_client.py
import os
import uuid
import requests
import logging
from dotenv import load_dotenv
from typing import Optional

load_dotenv()
logger = logging.getLogger(__name__)


class SaluteSpeechClient:
    """
    Клиент для работы с SaluteSpeech API (STT + TTS).
    Работает в локальном окружении (PyCharm)
    """

    def __init__(self):
        # URLs из документации Sber
        self.auth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        self.stt_url = "https://smartspeech.sber.ru/rest/v1/speech:recognize"
        self.tts_url = "https://smartspeech.sber.ru/rest/v1/text:synthesize"

        # Авторизация: берем из .env
        self.auth_token = os.getenv("SALUTE_AUTH_TOKEN")
        self.scope = "SALUTE_SPEECH_PERS"

        # Кэшируем access_token, чтобы не запрашивать каждый раз
        self._access_token: Optional[str] = None

        # Параметры аудио (требования SaluteSpeech)
        self.sample_rate = 16000  # 16 kHz
        self.channels = 1  # Mono
        self.bit_depth = 16  # 16-bit PCM

    def _get_access_token(self) -> str:
        """
        Получает OAuth access_token для вызова API.
        Кэширует токен в памяти до истечения срока жизни.
        """
        if self._access_token:
            return self._access_token

        if not self.auth_token:
            raise ValueError("SALUTE_AUTH_TOKEN не настроен в .env")

        rq_uid = str(uuid.uuid4())

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "RqUID": rq_uid,
            "Authorization": f"Basic {self.auth_token}"
        }

        payload = {
            "scope": self.scope
        }

        try:
            # verify=False нужен, если нет сертификатов Sber (для разработки)
            # В продакшене лучше настроить сертификаты!
            response = requests.post(
                self.auth_url,
                headers=headers,
                data=payload,
                verify=False,
                timeout=30
            )
            response.raise_for_status()

            token_data = response.json()
            self._access_token = token_data["access_token"]
            logger.info("SaluteSpeech access_token получен")
            return self._access_token

        except requests.RequestException as e:
            logger.error(f"Ошибка получения токена: {e}")
            raise RuntimeError(f"Не удалось получить SaluteSpeech токен: {e}")

    def speech_to_text(self, audio_path: str) -> str:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Аудиофайл не найден: {audio_path}")

        try:
            from pydub import AudioSegment
            import io

            logger.info(f"🔄 Конвертация: {os.path.basename(audio_path)}")
            audio = AudioSegment.from_file(audio_path)
            audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)

            buffer = io.BytesIO()
            audio.export(buffer, format="wav", codec="pcm_s16le")
            buffer.seek(0)
            audio_data = buffer.read()
            logger.info(f"✅ Конвертировано: {len(audio_data)} байт")
        except Exception as e:
            logger.error(f"❌ Ошибка конвертации: {e}")
            raise RuntimeError(f"Не удалось обработать аудио. Ошибка: {e}")

        token = self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "audio/x-pcm;bit=16;rate=16000;channels=1"
        }
        params = {"lang": "ru-RU", "profanityFilter": "true"}

        try:
            response = requests.post(
                self.stt_url, headers=headers, params=params,
                data=audio_data, verify=False, timeout=60
            )
            if response.status_code != 200:
                raise RuntimeError(f"Sber API Error {response.status_code}: {response.text}")

            result = response.json()
            if "result" in result and result["result"]:
                return " ".join(result["result"]).strip()
            return ""
        except Exception as e:
            logger.error(f"❌ STT Error: {e}")
            raise RuntimeError(f"Не удалось распознать речь: {e}")

    def text_to_speech(self, text: str, output_path: str, voice: str = "Nec_24000") -> str:
        """
        Синтезирует речь из текста и сохраняет в WAV-файл.

        Args:
            text: Текст для озвучки
            output_path: Путь для сохранения выходного файла
            voice: Голос (Nec_24000, May_24000, Bys_24000 и др.)

        Returns:
            Путь к сохраненному файлу
        """
        token = self._get_access_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/text"
        }

        params = {
            "format": "wav16",
            "voice": voice,
            "sampleRate": str(self.sample_rate)
        }

        try:
            logger.info(f"Синтез речи: '{text[:50]}...'")

            response = requests.post(
                self.tts_url,
                headers=headers,
                params=params,
                data=text.encode("utf-8"),
                verify=False,
                timeout=60
            )
            response.raise_for_status()

            # Сохраняем бинарные данные в файл
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(response.content)

            logger.info(f"Аудио сохранено: {output_path}")
            return output_path

        except requests.RequestException as e:
            logger.error(f"Ошибка TTS: {e}")
            raise RuntimeError(f"Не удалось синтезировать речь: {e}")

    def ping(self) -> bool:
        """Проверка доступности сервиса (получение токена)"""
        try:
            self._get_access_token()
            return True
        except:
            return False


# Глобальный экземпляр для импорта
salute_client = SaluteSpeechClient()