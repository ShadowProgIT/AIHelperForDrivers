package com.drivingassistant.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;
import io.swagger.v3.oas.annotations.media.Schema;


@Schema(description = "Запрос пользователя к ИИ-ассистенту вождения")
public record ChatRequestDto(

        @Schema(
                description = "Уникальный идентификатор сессии пользователя",
                example = "user-12345-session-abc",
                requiredMode = Schema.RequiredMode.NOT_REQUIRED
        )
        @JsonProperty("sessionId")
        String sessionId,

        @Schema(
                description = "Текст сообщения или вопроса пользователя",
                example = "Как правильно парковаться задним ходом?",
                requiredMode = Schema.RequiredMode.REQUIRED
        )
        @NotBlank(message = "Текст сообщения не может быть пустым")
        @JsonProperty("content")
        String content,

        @Schema(
                description = "Опциональный URL изображения (для анализа дорожной ситуации)",
                example = "https://example.com/road-image.jpg",
                requiredMode = Schema.RequiredMode.NOT_REQUIRED
        )
        @JsonProperty("image_url")
        String imageUrl

) {}
