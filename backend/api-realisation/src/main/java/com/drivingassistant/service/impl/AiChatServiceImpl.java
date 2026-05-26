package com.drivingassistant.service.impl;

import com.drivingassistant.dto.ChatMessageDto;
import com.drivingassistant.dto.ChatRequestDto;
import com.drivingassistant.dto.ChatResponseDto;
import com.drivingassistant.entity.Message;
import com.drivingassistant.enums.AiModelType;
import com.drivingassistant.enums.SenderType;
import com.drivingassistant.exceptions.SessionExpiredException;
import com.drivingassistant.repository.MessageRepository;
import com.drivingassistant.service.contract.AiChatService;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.reactive.function.client.WebClient;
import java.time.Duration;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

@Service
@Transactional
public class AiChatServiceImpl implements AiChatService {

    private final WebClient aiWebClient;
    private final SessionManager sessionManager;
    private final MessageRepository messageRepository;

    public AiChatServiceImpl(
            @Qualifier("aiWebClient") WebClient aiWebClient,
            SessionManager sessionManager,
            MessageRepository messageRepository) {
        this.aiWebClient = aiWebClient;
        this.sessionManager = sessionManager;
        this.messageRepository = messageRepository;
    }

    @Override
    public ChatResponseDto processChatRequest(ChatRequestDto request) {
        String sessionId = request.sessionId();
        if (!sessionManager.isValidSession(sessionId)) {
            sessionId = sessionManager.createSession();
        } else {
            sessionManager.touchSession(sessionId);
        }
        final String finalSessionId = sessionId;

        // Если фронт не передал модель, по умолчанию используем локальную
        AiModelType modelType = request.modelType() != null ? request.modelType() : AiModelType.LOCAL;

        String userContent = request.content() != null ? request.content() : "🎙️ Голосовое сообщение";
        messageRepository.save(new Message(finalSessionId, SenderType.USER, userContent, request.audioFile()));

        if ("AUDIO".equalsIgnoreCase(request.requestType())) {
            CompletableFuture.runAsync(() -> processVoiceAsync(finalSessionId, request.audioFile(), modelType));
            return new ChatResponseDto(finalSessionId, "🎙️ Обработка голосового запроса...", null);
        }

        ChatResponseDto aiResponse = callAi(finalSessionId, "TEXT", request.content(), null, modelType);
        messageRepository.save(new Message(finalSessionId, SenderType.AI, aiResponse.content(), aiResponse.audioResponse()));
        return aiResponse;
    }

    /** Асинхронный вызов для голоса */
    private void processVoiceAsync(String sessionId, String audioFile, AiModelType modelType) {
        try {
            ChatResponseDto resp = callAi(sessionId, "AUDIO", null, audioFile, modelType);
            if (resp != null) {
                String content = resp.content() != null ? resp.content() : "🎧 Голосовой ответ от ИИ";
                messageRepository.save(new Message(sessionId, SenderType.AI, content, resp.audioResponse()));
            }
        } catch (Exception e) {
            System.err.println("❌ Ошибка асинхронной обработки голоса: " + e.getMessage());
            messageRepository.save(new Message(sessionId, SenderType.AI, "⚠️ Ошибка обработки аудио", null));
        }
    }

    /** Универсальный вызов Python */
    private ChatResponseDto callAi(String sessionId, String requestType, String content, String audioFile, AiModelType modelType) {
        Map<String, Object> payload = new HashMap<>();
        payload.put("sessionId", sessionId);
        payload.put("requestType", requestType);
        if (content != null) payload.put("content", content);
        if (audioFile != null) payload.put("audio_file", audioFile);
        payload.put("modelType", modelType.getValue());

        return aiWebClient.post()
                .uri("/predict")
                .bodyValue(payload)
                .retrieve()
                .bodyToMono(ChatResponseDto.class)
                .block(Duration.ofSeconds(10000));
    }

    @Override
    @Transactional(readOnly = true)
    public List<ChatMessageDto> getChatHistory(String sessionId) {
        if (!sessionManager.isValidSession(sessionId)) {
            throw new SessionExpiredException("Сессия не найдена или истекла");
        }
        return messageRepository.findBySessionIdOrderByTimestampAsc(sessionId).stream()
                .map(m -> new ChatMessageDto(
                        String.valueOf(m.getId()),
                        m.getSessionId(),
                        m.getSender(),
                        m.getContent(),
                        m.getAudioFile(),
                        m.getTimestamp()
                ))
                .toList();
    }
}
