package com.drivingassistant.dto;

import com.drivingassistant.enums.RequestType;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonValue;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record ChatRequest(
        @NotBlank(message = "Session ID не может быть пустым")
        @JsonProperty("sessionId")
        String sessionId,

        @NotBlank(message = "Текст сообщения не может быть пустым")
        @JsonProperty("content")
        String content,

        @NotNull(message = "Тип запроса должен быть указан")
        @JsonProperty("requestMode")
        RequestType requestType,

        @JsonProperty("image_url")
        String imagePath
) {
}
