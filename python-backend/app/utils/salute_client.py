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
        """
        Распознаёт речь из WAV-файла.

        Требования к файлу:
        - Формат: WAV
        - Частота: 16000 Гц
        - Каналы: 1 (моно)
        - Битность: 16 бит
        - Кодировка: PCM

        Returns:
            Распознанный текст (строка)
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Аудиофайл не найден: {audio_path}")

        token = self._get_access_token()

        # Заголовки для STT
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": f"audio/x-pcm;bit={self.bit_depth};rate={self.sample_rate};channels={self.channels}"
        }

        # Параметры запроса
        params = {
            "lang": "ru-RU",  # Язык
            "profanityFilter": "true",  # Фильтр мата
        }

        try:
            with open(audio_path, "rb") as f:
                audio_data = f.read()

            logger.info(f"Отправка аудио на распознавание: {audio_path}")

            response = requests.post(
                self.stt_url,
                headers=headers,
                params=params,
                data=audio_data,
                verify=False,
                timeout=60
            )
            response.raise_for_status()

            result = response.json()

            if "result" in result and result["result"]:
                # Объединяем все распознанные фразы в один текст
                recognized_text = " ".join(result["result"]).strip()
                logger.info(f"Распознано: '{recognized_text}'")
                return recognized_text
            else:
                logger.warning("Распознавание вернуло пустой результат")
                return ""

        except requests.RequestException as e:
            logger.error(f"Ошибка STT: {e}")
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