package com.drivingassistant.repository;

import com.drivingassistant.entity.Message;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.List;

@Repository
public interface MessageRepository extends JpaRepository<Message, Long> {


    // Получить все сообщения сессии, отсортированные по времени (хронологический порядок)
    @Query("SELECT m FROM Message m WHERE m.sessionId = :sessionId ORDER BY m.timestamp ASC")
    List<Message> findBySessionIdOrderByTimestampAsc(String sessionId);

    //Получить последние N сообщений сессии (для пагинации)
    @Query(value = "SELECT * FROM messages WHERE session_id = :sessionId ORDER BY timestamp DESC LIMIT :limit",
            nativeQuery = true)
    List<Message> findTopBySessionIdOrderByTimestampDescNative(@Param("sessionId") String sessionId, @Param("limit") int limit);


    // Получить сообщения после определённого времени (для инкрементальной загрузки)
    @Query("SELECT m FROM Message m WHERE m.sessionId = :sessionId AND m.timestamp > :since ORDER BY m.timestamp ASC")
    List<Message> findBySessionIdAndTimestampAfter(String sessionId, Instant since);

    @Modifying
    @Query("DELETE FROM Message m WHERE m.sessionId = :sessionId")
    int deleteBySessionId(@Param("sessionId") String sessionId);

    @Modifying
    @Query(
            value = """
        DELETE FROM messages 
        WHERE ctid IN (
            SELECT ctid FROM messages 
            WHERE timestamp < :cutoff 
            LIMIT :limit
        )
        """,
            nativeQuery = true
    )
    int deleteBatchOlderThan(@Param("cutoff") Instant cutoff, @Param("limit") int limit);

    @Query("SELECT COUNT(m) > 0 FROM Message m WHERE m.timestamp < :cutoff")
    boolean existsOlderThan(@Param("cutoff") Instant cutoff);
}
