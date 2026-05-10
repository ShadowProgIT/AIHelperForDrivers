package com.drivingassistant.endpoints;

import com.drivingassistant.config.AiHelperContractConfig;
import com.drivingassistant.dto.ChatMessageDto;
import com.drivingassistant.dto.ChatRequestDto;
import com.drivingassistant.dto.ChatResponseDto;
import com.drivingassistant.dto.ErrorResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;

import jakarta.validation.Valid;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@Tag(name = "Chat", description = "Логика работы с чатом")
@RequestMapping(value = "/api/chat", produces = MediaType.APPLICATION_JSON_VALUE)
public interface ChatApi {

    @Operation(
            summary = "Отправить сообщение в чат с ИИ‑ассистентом",
            description = "Отправляет запрос пользователя к ИИ (теория или практика) и возвращает ответ.",
            security = @SecurityRequirement(name = AiHelperContractConfig.SECURITY_SCHEME_BEARER)
    )
    @ApiResponse(
            responseCode = "200",
            description = "Успешный ответ от ИИ‑ассистента",
            content = @Content(
                    mediaType = MediaType.APPLICATION_JSON_VALUE,
                    schema = @Schema(implementation = ChatResponseDto.class)
            )
    )
    @ApiResponse(
            responseCode = "400",
            description = "Ошибка валидации запроса",
            content = @Content(
                    mediaType = MediaType.APPLICATION_JSON_VALUE,
                    schema = @Schema(implementation = ErrorResponse.class)
            )
    )
    @PostMapping(
            value = "/",
            consumes = MediaType.APPLICATION_JSON_VALUE,
            produces = MediaType.APPLICATION_JSON_VALUE
    )
    ResponseEntity<ChatResponseDto> sendChatMessage(
            @Parameter(
                    description = "Тело запроса к ИИ‑ассистенту",
                    required = true
            )
            @Valid
            @RequestBody ChatRequestDto request
    );



    @Operation(
            summary = "Получить историю сообщений в сессии",
            description = "Возвращает список всех сообщений (пользователь + ИИ) " +
                    "в рамках указанной сессии для просмотра истории чата."
    )
    @ApiResponse(
            responseCode = "200",
            description = "История сообщений успешно получена",
            content = @Content(
                    mediaType = MediaType.APPLICATION_JSON_VALUE,
                    schema = @Schema(implementation = ChatMessageDto.class, type = "array")
            )
    )
    @ApiResponse(
            responseCode = "404",
            description = "Сессия не найдена",
            content = @Content(
                    mediaType = MediaType.APPLICATION_JSON_VALUE,
                    schema = @Schema(implementation = ErrorResponse.class)
            )
    )
    @GetMapping(
            value = "/{sessionId}",
            produces = MediaType.APPLICATION_JSON_VALUE
    )
    ResponseEntity<List<ChatMessageDto>> getChatHistory(
            @Parameter(
                    description = "Уникальный идентификатор сессии пользователя",
                    example = "user-12345-session-abc",
                    required = true
            )
            @PathVariable String sessionId
    );
}
