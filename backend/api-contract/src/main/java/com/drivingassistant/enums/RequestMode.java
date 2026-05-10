package com.drivingassistant.enums;

import com.fasterxml.jackson.annotation.JsonValue;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "Режим запроса к ИИ-ассистенту")
public enum RequestMode {

    @Schema(description = "Режим: теоретические вопросы ПДД")
    THEORY("THEORY"),

    @Schema(description = "Режим: практические ситуации на дороге")
    PRACTICE("PRACTICE");

    private final String value;

    RequestMode(String value) {
        this.value = value;
    }

    @JsonValue
    @Schema(hidden = true)
    public String getValue() {
        return value;
    }

    public static RequestMode fromString(String text) {
        if (text != null) {
            for (RequestMode type : RequestMode.values()) {
                if (text.equalsIgnoreCase(type.value)) {
                    return type;
                }
            }
        }
        throw new IllegalArgumentException("Несуществующий тип запроса: " + text);
    }
    }
