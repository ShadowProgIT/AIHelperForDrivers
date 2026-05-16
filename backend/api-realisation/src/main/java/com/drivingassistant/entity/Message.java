package com.drivingassistant.entity;

import com.drivingassistant.enums.SenderType;
import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(
        name = "messages",
        indexes = {
                @Index(name = "idx_messages_session_timestamp", columnList = "session_id, timestamp"),
                @Index(name = "idx_messages_timestamp", columnList = "timestamp")
        }
)
public class Message {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "session_id", nullable = false, length = 64)
    private String sessionId;

    @Column(name = "sender", nullable = false)
    @Enumerated(EnumType.STRING)
    private SenderType sender;

    @Column(name = "content", nullable = false, columnDefinition = "TEXT")
    private String content;

    @Column(name = "timestamp", nullable = false, updatable = false)
    private Instant timestamp;

    @Column(name = "audio_file")
    private String audioFile;

    public Message() {}

    public Message(String sessionId, SenderType sender, String content, String audioFile) {
        this.sessionId = sessionId;
        this.sender = sender;
        this.content = content;
        this.audioFile = audioFile;
        this.timestamp = Instant.now();
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getSessionId() {
        return sessionId;
    }

    public void setSessionId(String sessionId) {
        this.sessionId = sessionId;
    }

    public SenderType getSender() {
        return sender;
    }

    public void setSender(SenderType sender) {
        this.sender = sender;
    }

    public String getContent() {
        return content;
    }

    public void setContent(String content) {
        this.content = content;
    }

    public Instant getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(Instant timestamp) {
        this.timestamp = timestamp;
    }

    public String getAudioFile() {
        return audioFile;
    }

    public void setAudioFile(String audioFile) {
        this.audioFile = audioFile;
    }
}
