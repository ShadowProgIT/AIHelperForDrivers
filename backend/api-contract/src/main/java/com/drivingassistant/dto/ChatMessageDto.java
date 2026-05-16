package com.drivingassistant.dto;

import com.drivingassistant.enums.SenderType;
import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;

import java.time.Instant;

@Schema(description = "Сообщение в чате как история (от пользователя или ИИ)")
public record ChatMessageDto(
        @Schema(description = "Идентификатор сообщения", example = "msg-12345")
        @JsonProperty("id") String id,

        @Schema(description = "Идентификатор сессии пользователя", example = "user-12345-session-abc")
        @JsonProperty("sessionId") String sessionId,

        @Schema(description = "Тип отправителя сообщения", allowableValues = {"USER", "AI"})
        @JsonProperty("sender") SenderType sender,

        @Schema(description = "Текст сообщения или вопроса пользователя", example = "Как правильно парковаться задним ходом?")
        @JsonProperty("content") String content,

        @Schema(description = "Имя файла с голосовым ответом (из папки output)", example = "a1b2c3d4-e5f6-7890-abcd-ef1234567890.wav")
        @JsonProperty("audio_file") String audioFile,

        @Schema(description = "Метка времени создания сообщения")
        @JsonProperty("timestamp") Instant timestamp
) {}
