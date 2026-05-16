package com.drivingassistant.service.impl;

import com.drivingassistant.service.contract.VoiceService;
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

    private final Path inputDir = Paths.get("data/voice-input");
    private final Path outputDir = Paths.get("data/voice-output");

    public VoiceServiceImpl() throws IOException {
        Files.createDirectories(inputDir, outputDir);
    }

    @Override
    public String saveInput(MultipartFile file) throws IOException {
        String taskId = UUID.randomUUID().toString();
        // Сохраняем байты как .wav (внешний сервис читает по заголовкам)
        file.transferTo(inputDir.resolve(taskId + ".wav"));
        return taskId;
    }

    @Override
    public boolean isReady(String taskId) {
        return Files.exists(outputDir.resolve(taskId + ".wav"));
    }

    @Override
    public Resource getResponseAudio(String taskId) throws IOException {
        Path file = outputDir.resolve(taskId + ".wav");
        if (!Files.exists(file)) {
            throw new IOException("Audio not ready: " + taskId);
        }
        return new UrlResource(file.toUri());
    }
}
