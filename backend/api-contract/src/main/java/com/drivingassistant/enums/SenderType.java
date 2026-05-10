package com.drivingassistant.enums;

import com.fasterxml.jackson.annotation.JsonValue;
import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "Тип отправителя сообщения в чате")
public enum SenderType {

    @Schema(description = "Сообщение от пользователя")
    USER("USER"),

    @Schema(description = "Сообщение от ИИ‑ассистента")
    AI("AI");

    @JsonValue
    public final String value;

    SenderType(String value) {
        this.value = value;
    }
}
