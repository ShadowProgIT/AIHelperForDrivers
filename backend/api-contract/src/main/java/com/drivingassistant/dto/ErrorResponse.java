package com.drivingassistant.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;

import java.time.Instant;
import java.util.List;

@Schema(description = "Стандартный объект ошибки API")
public record ErrorResponse(

        @Schema(description = "Код ошибки (например, BAD_REQUEST, NOT_FOUND)", example = "BAD_REQUEST")
        @JsonProperty("code")
        String code,

        @Schema(description = "Понятное человеку сообщение об ошибке", example = "Session ID не может быть пустым")
        @JsonProperty("message")
        String message,

        @Schema(description = "Опциональный детальный путь/параметр, где возникла ошибка", example = "sessionId")
        @JsonProperty("field")
        String field,

        @Schema(description = "Момент возникновения ошибки (UTC)", example = "2026-03-03T10:15:30Z")
        Instant timestamp,

        @Schema(description = "Ошибки по отдельным полям (заполняется только для 400 Bad Request с ошибками валидации)")
        List<FieldError> fieldErrors
) {
    @Schema(description = "Ошибка валидации поля")
    public record FieldError(

            @Schema(description = "Имя невалидного поля", example = "weight")
            String field,

            @Schema(description = "Значение, которое было отклонено", example = "-5")
            Object rejectedValue,

            @Schema(description = "Причина отклонения", example = "Некорректный вес. Допустимые значения: weight:5, weight:27")
            String message
    ) {}
}
