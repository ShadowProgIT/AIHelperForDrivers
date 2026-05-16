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

@Service
public class VoiceServiceImpl implements VoiceService {

    private final String inputDirStr;
    private final String outputDirStr;

    // Поля инициализируются в @PostConstruct, а не в конструкторе
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
        this.outputDir = Paths.get(outputDirStr).toAbsolutePath().normalize();

        Files.createDirectories(this.inputDir);
    }

    @Override
    public String saveInput(MultipartFile file) throws IOException {
        String taskId = UUID.randomUUID().toString();
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
