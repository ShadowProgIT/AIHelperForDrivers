package com.drivingassistant.service.impl;

import com.drivingassistant.dto.ChatMessageDto;
import com.drivingassistant.dto.ChatRequestDto;
import com.drivingassistant.dto.ChatResponseDto;
import com.drivingassistant.entity.Message;
import com.drivingassistant.enums.RequestMode;
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

        // 1. Сохраняем сообщение пользователя в БД
        // Если голосовое, подставляем плейсхолдер, чтобы не нарушать nullable=false в entity
        String userContent = request.content() != null ? request.content() : "🎙️ Голосовое сообщение";
        messageRepository.save(new Message(finalSessionId, SenderType.USER, userContent, request.audioFile()));

        // 2. Ветвление по типу запроса
        if ("AUDIO".equalsIgnoreCase(request.requestType())) {
            // Запускаем фоновую обработку и сразу возвращаем PENDING
            CompletableFuture.runAsync(() -> processVoiceAsync(finalSessionId, request.audioFile()));
            return new ChatResponseDto(finalSessionId, RequestMode.THEORY, "🎙️ Обработка голосового запроса...", null);
        }

        // 3. Синхронная обработка текста
        ChatResponseDto aiResponse = callAi(finalSessionId, "TEXT", request.content(), null);
        messageRepository.save(new Message(finalSessionId, SenderType.AI, aiResponse.content(), aiResponse.audioResponse()));
        return aiResponse;
    }

    /** Асинхронный вызов для голоса (выполняется в отдельном потоке) */
    private void processVoiceAsync(String sessionId, String audioFile) {
        try {
            ChatResponseDto resp = callAi(sessionId, "AUDIO", null, audioFile);
            if (resp != null) {
                String content = resp.content() != null ? resp.content() : "🎧 Голосовой ответ от ИИ";
                messageRepository.save(new Message(sessionId, SenderType.AI, content, resp.audioResponse()));
            }
        } catch (Exception e) {
            System.err.println("❌ Ошибка асинхронной обработки голоса: " + e.getMessage());
            // В случае ошибки можно сохранить сообщение-заглушку, чтобы фронт не висел
            messageRepository.save(new Message(sessionId, SenderType.AI, "⚠️ Ошибка обработки аудио", null));
        }
    }

    /** Универсальный вызов Python. Собирает JSON строго по флагу */
    private ChatResponseDto callAi(String sessionId, String requestType, String content, String audioFile) {
        Map<String, Object> payload = new HashMap<>();
        payload.put("sessionId", sessionId);
        payload.put("requestType", requestType);
        // Добавляем поля ТОЛЬКО если они не null
        if (content != null) payload.put("content", content);
        if (audioFile != null) payload.put("audio_file", audioFile);
        payload.put("requestMode", RequestMode.THEORY.name());

        return aiWebClient.post()
                .uri("/predict") // Python сам разбирает requestType
                .bodyValue(payload)
                .retrieve()
                .bodyToMono(ChatResponseDto.class)
                .block(Duration.ofSeconds(15));
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
