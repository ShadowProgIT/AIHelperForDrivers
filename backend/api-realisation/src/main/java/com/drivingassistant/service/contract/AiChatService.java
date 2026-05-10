package com.drivingassistant.service.contract;

import com.drivingassistant.dto.ChatRequestDto;
import com.drivingassistant.dto.ChatResponseDto;
import com.drivingassistant.dto.ChatMessageDto;
import java.util.List;

public interface AiChatService {
    ChatResponseDto processChatRequest(ChatRequestDto request);
    List<ChatMessageDto> getChatHistory(String sessionId);
}
