package com.drivingassistant.service.contract;

import org.springframework.core.io.Resource;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;

public interface VoiceService {

    /**
     * Сохраняет входной аудиофайл от пользователя.
     * @param file загруженный файл
     * @return UUID taskId (без расширения), который будет использоваться как имя файла
     * @throws IOException если не удалось сохранить
     */
    String saveInput(MultipartFile file) throws IOException;

    /**
     * Проверяет, готов ли аудио-ответ от Python.
     * Python должен сохранить файл {taskId}.wav в output-dir.
     * @param taskId UUID, возвращённый из saveInput()
     * @return true если файл существует в output-dir
     */
    boolean isReady(String taskId);

    /**
     * Возвращает ресурс с аудио-ответом для отправки на фронтенд.
     * @param taskId UUID задачи
     * @return Resource с файлом из output-dir
     * @throws IOException если файл не найден или не готов
     */
    Resource getResponseAudio(String taskId) throws IOException;

    /**
     * Возвращает абсолютный путь к входной директории (для отладки/логирования).
     */
    String getInputDirPath();

    /**
     * Возвращает абсолютный путь к выходной директории (для отладки/логирования).
     */
    String getOutputDirPath();
}
