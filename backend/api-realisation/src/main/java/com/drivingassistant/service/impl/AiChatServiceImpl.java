package com.drivingassistant.service.impl;

import com.drivingassistant.dto.ChatMessageDto;
import com.drivingassistant.dto.ChatRequestDto;
import com.drivingassistant.dto.ChatResponseDto;
import com.drivingassistant.entity.Message;
import com.drivingassistant.enums.RequestMode;
import com.drivingassistant.enums.SenderType;
import com.drivingassistant.repository.MessageRepository;
import com.drivingassistant.service.contract.AiChatService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@Transactional
public class AiChatServiceImpl implements AiChatService {

    private final WebClient aiWebClient;
    private final SessionManager sessionManager;
    private final MessageRepository messageRepository;

    public AiChatServiceImpl(
            WebClient.Builder webClientBuilder,
            SessionManager sessionManager,
            MessageRepository messageRepository,
            @Value("${ai.service.url:http://localhost:8000}") String aiServiceUrl
    ) {
        this.aiWebClient = webClientBuilder.baseUrl(aiServiceUrl).build();
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

        RequestMode mode = (request.imageUrl() != null && !request.imageUrl().isBlank())
                ? RequestMode.PRACTICE
                : RequestMode.THEORY;

        Message userMessage = new Message(sessionId, SenderType.USER, request.content(), request.imageUrl());
        messageRepository.save(userMessage);

        Map<String, Object> pythonPayload = Map.of(
                "sessionId", sessionId,
                "content", request.content(),
                "mode", mode.name(),
                "image_url", request.imageUrl()
        );

        ChatResponseDto aiResponse = aiWebClient.post()
                .uri("/predict")
                .bodyValue(pythonPayload)
                .retrieve()
                .bodyToMono(ChatResponseDto.class)
                .block();

        if (aiResponse == null) {
            aiResponse = new ChatResponseDto(
                    sessionId,
                    mode,
                    "Ошибка: не получен ответ от ИИ-сервиса",
                    null
            );
        }

        Message aiMessage = new Message(sessionId, SenderType.AI, aiResponse.content(), aiResponse.imageUrl());
        messageRepository.save(aiMessage);

        return new ChatResponseDto(
                sessionId,
                mode,
                aiResponse.content(),
                aiResponse.imageUrl()
        );
    }

    @Override
    @Transactional(readOnly = true)
    public List<ChatMessageDto> getChatHistory(String sessionId) {
        // Валидация сессии
        if (!sessionManager.isValidSession(sessionId)) {
            return List.of(); // или бросить исключение
        }

        // Получаем историю из БД, отсортированную по времени
        List<Message> messages = messageRepository.findBySessionIdOrderByTimestampAsc(sessionId);

        return messages.stream()
                .map(m -> new ChatMessageDto(
                        String.valueOf(m.getId()),
                        m.getSessionId(),
                        m.getSender(),
                        m.getContent(),
                        m.getImageUrl(),
                        m.getTimestamp()
                ))
                .collect(Collectors.toList());
    }
}
