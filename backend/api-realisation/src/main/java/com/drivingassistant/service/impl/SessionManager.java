package com.drivingassistant.service.impl;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.UUID;

@Service
public class SessionManager {

    private static final String KEY_PREFIX = "session:";

    private final StringRedisTemplate redisTemplate;
    private final Duration sessionTtl;

    public SessionManager(
            StringRedisTemplate redisTemplate,
            @Value("${session.ttl.seconds:7200}") long sessionTtlSeconds
    ) {
        this.redisTemplate = redisTemplate;
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

    public void deleteSession(String sessionId) {
        if (sessionId != null && !sessionId.isBlank()) {
            redisTemplate.delete(buildKey(sessionId));
        }
    }

    private String buildKey(String sessionId) {
        return KEY_PREFIX + sessionId;
    }
}