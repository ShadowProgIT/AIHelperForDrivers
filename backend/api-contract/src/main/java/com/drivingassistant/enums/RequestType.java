package com.drivingassistant.enums;

import com.fasterxml.jackson.annotation.JsonValue;

public enum RequestType {
    THEORY("THEORY"),
    PRACTICE("PRACTICE");

    private final String value;

    RequestType(String value) {
        this.value = value;
    }

    @JsonValue
    public String getValue() {
        return value;
    }

    public static RequestType fromString(String text) {
        if (text != null) {
            for (RequestType type : RequestType.values()) {
                if (text.equalsIgnoreCase(type.value)) {
                    return type;
                }
            }
        }

        throw new IllegalArgumentException("Несуществующий тип запроса: " + text);
    }
}
