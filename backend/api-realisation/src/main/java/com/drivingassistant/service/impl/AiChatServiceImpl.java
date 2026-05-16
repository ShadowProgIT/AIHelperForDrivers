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
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.stream.Collectors;

@Service
@Transactional
public class AiChatServiceImpl implements AiChatService {

    private final WebClient aiWebClient;
    private final SessionManager sessionManager;
    private final MessageRepository messageRepository;

    public AiChatServiceImpl(
            @Qualifier("aiWebClient") WebClient aiWebClient,
            SessionManager sessionManager,
            MessageRepository messageRepository
    ) {
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

        // Только THEORY, т.к. изображений нет
        RequestMode mode = RequestMode.THEORY;

        // Сохраняем сообщение пользователя (с поддержкой audioFile)
        Message userMessage = new Message(sessionId, SenderType.USER, request.content(), request.audioFile());
        messageRepository.save(userMessage);

        // === Если это голосовое — запускаем асинхронную обработку ===
        if (request.audioFile() != null && !request.audioFile().isBlank()) {
            CompletableFuture.runAsync(() -> processVoiceAsync(sessionId, request.audioFile()));
            return new ChatResponseDto(sessionId, mode, "🎙️ Обработка...", "processing:" + request.audioFile());
        }

        // === Обычный текстовый запрос ===
        Map<String, Object> pythonPayload = Map.of(
                "sessionId", sessionId,
                "content", request.content(),
                "mode", mode.name(),
                "audio_file", request.audioFile()
        );

        ChatResponseDto aiResponse = aiWebClient.post()
                .uri("/predict")
                .bodyValue(pythonPayload)
                .retrieve()
                .bodyToMono(ChatResponseDto.class)
                .block();

        if (aiResponse == null) {
            aiResponse = new ChatResponseDto(sessionId, mode, "Ошибка ИИ-сервиса", null);
        }

        // Сохраняем ответ (с поддержкой audioResponse)
        Message aiMessage = new Message(sessionId, SenderType.AI, aiResponse.content(), aiResponse.audioResponse());
        messageRepository.save(aiMessage);

        return new ChatResponseDto(sessionId, mode, aiResponse.content(), aiResponse.audioResponse());
    }

    private void processVoiceAsync(String sessionId, String audioFile) {
        try {
            ChatResponseDto resp = aiWebClient.post()
                    .uri("/predict_voice")
                    .bodyValue(Map.of("sessionId", sessionId, "audio_file", audioFile))
                    .retrieve()
                    .bodyToMono(ChatResponseDto.class)
                    .block();

            if (resp != null && resp.audioResponse() != null) {
                Message aiVoice = new Message(sessionId, SenderType.AI,
                        resp.content() != null ? resp.content() : "🎧 Ответ",
                        resp.audioResponse());
                messageRepository.save(aiVoice);
            }
        } catch (Exception e) {
            System.err.println("Ошибка обработки голоса: " + e.getMessage());
        }
    }

    @Override
    @Transactional(readOnly = true)
    public List<ChatMessageDto> getChatHistory(String sessionId) {
        if (!sessionManager.isValidSession(sessionId)) {
            throw new SessionExpiredException("Сессия не найдена");
        }
        return messageRepository.findBySessionIdOrderByTimestampAsc(sessionId).stream()
                .map(m -> new ChatMessageDto(
                        String.valueOf(m.getId()),
                        m.getSessionId(),
                        m.getSender(),
                        m.getContent(),
                        m.getAudioFile(),  // ← передаём аудиофайл
                        m.getTimestamp()
                ))
                .collect(Collectors.toList());
    }
}
