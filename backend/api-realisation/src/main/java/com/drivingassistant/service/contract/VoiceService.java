package com.drivingassistant.service.contract;

import org.springframework.core.io.Resource;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;

public interface VoiceService {
    String saveInput(MultipartFile file) throws IOException;
    boolean isReady(String taskId);
    Resource getResponseAudio(String taskId) throws IOException;
}
