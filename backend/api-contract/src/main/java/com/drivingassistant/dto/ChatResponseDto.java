package com.drivingassistant.dto;

import com.drivingassistant.enums.RequestMode;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;



@Schema(description = "Ответ ИИ-ассистента на запрос пользователя")
@JsonInclude(JsonInclude.Include.NON_NULL)
public record ChatResponseDto(
        @Schema(description = "Идентификатор сессии, к которой относится ответ", requiredMode = Schema.RequiredMode.REQUIRED)
        @JsonProperty("sessionId") String sessionId,

        @Schema(description = "Текстовый ответ от ИИ-модели", requiredMode = Schema.RequiredMode.REQUIRED)
        @JsonProperty("content") String content,

        @Schema(description = "Имя файла с синтезированным голосовым ответом (из папки output)", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
        @JsonProperty("audio_response") String audioResponse
) {}
