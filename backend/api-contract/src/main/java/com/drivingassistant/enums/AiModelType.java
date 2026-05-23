package com.drivingassistant.enums;

import com.fasterxml.jackson.annotation.JsonValue;
import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "Тип используемой ИИ-модели")
public enum AiModelType {
    @Schema(description = "Локальная модель (Local LLM)")
    LOCAL("LOCAL"),
    @Schema(description = "Облачная модель Yandex GigaChat")
    GIGACHAT("GLOBAL");

    private final String value;

    AiModelType(String value) { this.value = value; }

    @JsonValue
    @Schema(hidden = true)
    public String getValue() { return value; }

    public static AiModelType fromString(String text) {
        if (text == null) return LOCAL;
        for (AiModelType type : values()) {
            if (type.value.equalsIgnoreCase(text)) return type;
        }
        return LOCAL;
    }
}