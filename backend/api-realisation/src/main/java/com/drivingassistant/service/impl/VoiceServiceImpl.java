package com.drivingassistant.service.impl;

import com.drivingassistant.service.contract.VoiceService;
import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.UUID;

@Service
public class VoiceServiceImpl implements VoiceService {
    private static final Logger log = LoggerFactory.getLogger(VoiceServiceImpl.class);

    private final String inputDirStr;
    private final String outputDirStr;

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
        this.inputDir = Paths.get(inputDirStr).toAbsolutePath().normalize();
        Files.createDirectories(this.inputDir);
        log.info("Voice input directory ready: {}", inputDir);

        this.outputDir = Paths.get(outputDirStr).toAbsolutePath().normalize();
        if (Files.notExists(this.outputDir)) {
            Files.createDirectories(this.outputDir);
        }
        log.info("Voice output directory ready: {}", outputDir);
    }

    private Path resolveAudioPath(String taskId) {
        if (taskId == null || taskId.isBlank()) return null;
        String fileName = taskId.endsWith(".wav") ? taskId : taskId + ".wav";
        return outputDir.resolve(fileName);
    }

    @Override
    public String saveInput(MultipartFile file) throws IOException {
        if (file.isEmpty()) throw new IOException("Пустой аудиофайл");
        String taskId = UUID.randomUUID().toString();
        String fileName = taskId + ".wav";
        Path destination = inputDir.resolve(fileName);
        file.transferTo(destination);
        log.debug("Saved input audio: {} → {}", fileName, destination);
        return taskId;
    }

    @Override
    public boolean isReady(String taskId) {
        if (taskId == null || taskId.isBlank()) return false;
        Path audioFile = resolveAudioPath(taskId);
        boolean ready = Files.exists(audioFile);
        log.debug(ready ? "Audio ready: {}" : "Audio not ready: {}", audioFile);
        return ready;
    }

    @Override
    public Resource getResponseAudio(String taskId) throws IOException {
        if (taskId == null || taskId.isBlank()) throw new IOException("taskId не может быть пустым");
        Path audioFile = resolveAudioPath(taskId);

        if (!Files.exists(audioFile)) {
            log.warn("Audio file not found: {}", audioFile);
            throw new IOException("Аудио-ответ не найден: " + taskId);
        }
        Resource resource = new UrlResource(audioFile.toUri());
        if (!resource.exists() || !resource.isReadable()) {
            throw new IOException("Не удалось прочитать аудиофайл: " + audioFile);
        }
        log.debug("Serving audio response: {}", audioFile);
        return resource;
    }

    @Override
    public String getInputDirPath() { return inputDir.toString(); }
    @Override
    public String getOutputDirPath() { return outputDir.toString(); }
}