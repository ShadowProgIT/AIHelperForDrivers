package com.drivingassistant.service.impl;

import com.drivingassistant.repository.MessageRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Duration;
import java.util.UUID;

@Service
public class SessionManager {

    private static final String KEY_PREFIX = "session:";

    private final StringRedisTemplate redisTemplate;
    private final MessageRepository messageRepository;
    private final Duration sessionTtl;

    public SessionManager(
            StringRedisTemplate redisTemplate,
            MessageRepository messageRepository,
            @Value("${session.ttl.seconds:7200}") long sessionTtlSeconds
    ) {
        this.redisTemplate = redisTemplate;
        this.messageRepository = messageRepository;
        this.sessionTtl = Duration.ofSeconds(sessionTtlSeconds > 0 ? sessionTtlSeconds : 7200);
    }

    public String createSession() {
        String sessionId = UUID.randomUUID().toString();
        String key = buildKey(sessionId);

        redisTemplate.opsForValue().set(key, "active", sessionTtl);

        return sessionId;
    }

    public boolean isValidSession(String sessionId) {
        if (sessionId == null || sessionId.isBlank()) {
            return false;
        }
        String key = buildKey(sessionId);
        Boolean exists = redisTemplate.hasKey(key);
        return Boolean.TRUE.equals(exists);
    }

    public void touchSession(String sessionId) {
        if (isValidSession(sessionId)) {
            String key = buildKey(sessionId);
            redisTemplate.expire(key, sessionTtl);
        }
    }

    private String buildKey(String sessionId) {
        return KEY_PREFIX + sessionId;
    }

    @Transactional // ← важно: атомарность БД + логика
    public void deleteSession(String sessionId) {
        if (sessionId == null || sessionId.isBlank()) return;

        // 1. Чистим PostgreSQL (в транзакции)
        int deleted = messageRepository.deleteBySessionId(sessionId);

        // 2. Чистим Redis
        redisTemplate.delete(buildKey(sessionId));
    }



}