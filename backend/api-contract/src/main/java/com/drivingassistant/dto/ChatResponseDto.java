package com.drivingassistant.dto;

import com.drivingassistant.enums.RequestMode;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "Ответ ИИ-ассистента на запрос пользователя")
@JsonInclude(JsonInclude.Include.NON_NULL)
public record ChatResponseDto(

        @Schema(
                description = "Идентификатор сессии, к которой относится ответ",
                example = "user-12345-session-abc",
                requiredMode = Schema.RequiredMode.REQUIRED
        )
        @JsonProperty("sessionId")
        String sessionId,

        @Schema(
                description = "Режим, в котором был обработан запрос",
                example = "THEORY",
                allowableValues = {"THEORY", "PRACTICE"},
                requiredMode = Schema.RequiredMode.REQUIRED
        )
        @JsonProperty("requestMode")
        RequestMode requestMode,

        @Schema(
                description = "Текстовый ответ от ИИ-модели",
                example = "Для парковки задним ходом: 1) Включите заднюю передачу...",
                requiredMode = Schema.RequiredMode.REQUIRED
        )
        @JsonProperty("content")
        String content,

        @Schema(
                description = "Опциональный URL изображения (если ИИ сгенерировал визуализацию)",
                example = "https://example.com/ai-response-image.jpg",
                requiredMode = Schema.RequiredMode.NOT_REQUIRED
        )
        @JsonProperty("image_url")
        String imageUrl

) {}
