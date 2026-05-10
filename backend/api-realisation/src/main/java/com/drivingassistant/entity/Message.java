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

    @Column(name = "image_url")
    private String imageUrl;

    @Column(name = "timestamp", nullable = false, updatable = false)
    private Instant timestamp;

    public Message() {
    }

    public Message(String sessionId, SenderType sender, String content, String imageUrl) {
        this.sessionId = sessionId;
        this.sender = sender;
        this.content = content;
        this.imageUrl = imageUrl;
        this.timestamp = Instant.now();
    }

    // Getters
    public Long getId() {
        return id;
    }

    public String getSessionId() {
        return sessionId;
    }

    public SenderType getSender() {
        return sender;
    }

    public String getContent() {
        return content;
    }

    public String getImageUrl() {
        return imageUrl;
    }

    public Instant getTimestamp() {
        return timestamp;
    }

    // Setters (если нужны)
    public void setContent(String content) {
        this.content = content;
    }

    public void setImageUrl(String imageUrl) {
        this.imageUrl = imageUrl;
    }
}
