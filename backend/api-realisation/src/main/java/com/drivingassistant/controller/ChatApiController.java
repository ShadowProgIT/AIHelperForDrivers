package com.drivingassistant.controller;

import com.drivingassistant.dto.ChatRequestDto;
import com.drivingassistant.dto.ChatResponseDto;
import com.drivingassistant.dto.ChatMessageDto;
import com.drivingassistant.endpoints.ChatApi;
import com.drivingassistant.service.contract.AiChatService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController

public class ChatApiController implements ChatApi {

    private final AiChatService chatService;

    public ChatApiController(AiChatService chatService) {
        this.chatService = chatService;
    }

    @Override
    public ResponseEntity<ChatResponseDto> sendChatMessage(
            @Valid @RequestBody ChatRequestDto request
    ) {
        ChatResponseDto response = chatService.processChatRequest(request);
        return ResponseEntity.ok(response);
    }

    @Override
    public ResponseEntity<List<ChatMessageDto>> getChatHistory(
            @PathVariable String sessionId
    ) {
        List<ChatMessageDto> history = chatService.getChatHistory(sessionId);
        return ResponseEntity.ok(history);
    }
}
