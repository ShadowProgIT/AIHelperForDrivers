package com.drivingassistant.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;
import com.fasterxml.jackson.annotation.JsonInclude;

@Schema(description = "Запрос пользователя к ИИ-ассистенту")
@JsonInclude(JsonInclude.Include.NON_NULL) 
public record ChatRequestDto(
        @Schema(description = "ID сессии")
        @JsonProperty("sessionId") String sessionId,

        @Schema(description = "Тип запроса: TEXT или AUDIO", requiredMode = Schema.RequiredMode.REQUIRED, allowableValues = {"TEXT", "AUDIO"})
        @JsonProperty("requestType") String requestType,

        @Schema(description = "Текст сообщения (только для TEXT)")
        @JsonProperty("content") String content,

        @Schema(description = "Имя аудиофайла (только для AUDIO)")
        @JsonProperty("audio_file") String audioFile
) {
        // Компактный конструктор для валидации
        public ChatRequestDto {
                if (requestType == null || requestType.isBlank()) {
                        throw new IllegalArgumentException("Поле requestType обязательно");
                }
                if ("TEXT".equalsIgnoreCase(requestType) && (content == null || content.isBlank())) {
                        throw new IllegalArgumentException("Для TEXT запроса поле content обязательно");
                }
                if ("AUDIO".equalsIgnoreCase(requestType) && (audioFile == null || audioFile.isBlank())) {
                        throw new IllegalArgumentException("Для AUDIO запроса поле audioFile обязательно");
                }
        }
}
