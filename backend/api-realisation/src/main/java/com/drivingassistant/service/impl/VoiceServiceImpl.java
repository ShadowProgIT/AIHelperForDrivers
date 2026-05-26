package com.drivingassistant.service.impl;

import com.drivingassistant.service.contract.VoiceService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import javax.annotation.PostConstruct;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Service
public class VoiceServiceImpl implements VoiceService {

    private static final Logger log = LoggerFactory.getLogger(VoiceServiceImpl.class);

    private final String inputDirStr;
    private final String outputDirStr;

    // Инициализируются в @PostConstruct
    private Path inputDir;
    private Path outputDir;

    public VoiceServiceImpl(
            @Value("${voice.input-dir:audio_input}") String inputDirStr,
            @Value("${voice.output-dir:audio_output}") String outputDirStr) {
        this.inputDirStr = inputDirStr;
        this.outputDirStr = outputDirStr;
    }

    @PostConstruct
    public void init() throws IOException {
        // input-dir создаём мы (Java)
        this.inputDir = Paths.get(inputDirStr).toAbsolutePath().normalize();
        Files.createDirectories(this.inputDir);
        log.info("✅ Voice input directory ready: {}", inputDir);

        // output-dir НЕ создаём — его создаёт Python!
        // Только логируем ожидаемый путь для отладки
        this.outputDir = Paths.get(outputDirStr).toAbsolutePath().normalize();
        log.info("📦 Voice output directory expected (managed by Python): {}", outputDir);
    }

    @Override
    public String saveInput(MultipartFile file) throws IOException {
        if (file.isEmpty()) {
            throw new IOException("Пустой аудиофайл");
        }

        // Генерируем уникальный taskId (UUID без расширения)
        String taskId = UUID.randomUUID().toString();
        String fileName = taskId + ".wav";

        // Сохраняем в input-dir
        Path destination = inputDir.resolve(fileName);
        file.transferTo(destination);

        log.debug("🎙️ Saved input audio: {} → {}", fileName, destination);
        return taskId; // возвращаем только UUID, без .wav
    }

    @Override
    public boolean isReady(String taskId) {
        if (taskId == null || taskId.isBlank()) {
            return false;
        }
        Path audioFile = outputDir.resolve(taskId + ".wav");
        boolean ready = Files.exists(audioFile);

        if (ready) {
            log.debug("✅ Audio response ready: {}", audioFile);
        } else {
            log.debug("⏳ Audio response not ready yet: {}", audioFile);
        }
        return ready;
    }

    @Override
    public Resource getResponseAudio(String taskId) throws IOException {
        if (taskId == null || taskId.isBlank()) {
            throw new IOException("taskId не может быть пустым");
        }

        Path audioFile = outputDir.resolve(taskId + ".wav");

        if (!Files.exists(audioFile)) {
            log.warn("❌ Audio file not found: {}", audioFile);
            throw new IOException("Аудио-ответ ещё не готов или не найден: " + taskId);
        }

        // UrlResource позволяет Spring корректно отдать файл с нужными заголовками
        Resource resource = new UrlResource(audioFile.toUri());
        if (!resource.exists() || !resource.isReadable()) {
            throw new IOException("Не удалось прочитать аудиофайл: " + audioFile);
        }

        log.debug("🔊 Serving audio response: {}", audioFile);
        return resource;
    }

    @Override
    public String getInputDirPath() {
        return inputDir.toString();
    }

    @Override
    public String getOutputDirPath() {
        return outputDir.toString();
    }
}
