package com.drivingassistant.service.impl;

import com.drivingassistant.repository.MessageRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.time.Duration;
import java.time.Instant;

@Service
public class HistoryCleanupScheduler {

    private static final Logger log = LoggerFactory.getLogger(HistoryCleanupScheduler.class);

    private final MessageRepository messageRepository;
    private final Duration retentionPeriod;
    private final int batchSize;

    public HistoryCleanupScheduler(
            MessageRepository messageRepository,
            @Value("${cleanup.history.retention.days:30}") int retentionDays,
            @Value("${cleanup.history.batch-size:1000}") int batchSize
    ) {
        this.messageRepository = messageRepository;
        this.retentionPeriod = Duration.ofDays(retentionDays);
        this.batchSize = batchSize;
    }

    @Scheduled(cron = "${cleanup.history.cron:0 0 3 * * ?}")
    @Transactional
    public void cleanupExpiredHistory() {
        Instant cutoff = Instant.now().minus(retentionPeriod);

        // Быстрая проверка: есть ли что удалять?
        if (!messageRepository.existsOlderThan(cutoff)) {
            log.debug("No messages older than {} found, skipping cleanup", cutoff);
            return;
        }

        long start = System.currentTimeMillis();
        int totalDeleted = 0;
        boolean hasMore;

        // Батч-удаление: чтобы не блокировать таблицу надолго
        do {
            int deleted = messageRepository.deleteBatchOlderThan(cutoff, batchSize);
            totalDeleted += deleted;
            hasMore = deleted == batchSize;

            if (hasMore) {
                // Даём БД "передохнуть" между батчами
                try {
                    Thread.sleep(50);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    log.warn("Cleanup interrupted after deleting {} records", totalDeleted);
                    break;
                }
            }
        } while (hasMore);

        long duration = System.currentTimeMillis() - start;
        log.info("History cleanup completed: {} records deleted in {} ms", totalDeleted, duration);
    }
}
