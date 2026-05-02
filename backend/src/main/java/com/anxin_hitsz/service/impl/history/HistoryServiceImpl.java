package com.anxin_hitsz.service.impl.history;

import com.anxin_hitsz.dto.history.SessionDTO;
import com.anxin_hitsz.service.history.IHistoryService;
import cn.hutool.json.JSONUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.concurrent.TimeUnit;

/**
 * ClassName: HistoryServiceImpl
 * Package: com.anxin_hitsz.service.impl.history
 * Description: 对话历史服务实现（Redis 存储）
 *
 * @Author AnXin
 * @Create 2026/5/2
 * @Version 1.0
 */
@Service
public class HistoryServiceImpl implements IHistoryService {

    private static final String HISTORY_KEY_PREFIX = "agent:chat:history:";
    private static final String SESSION_META_PREFIX = "agent:chat:session:";
    private static final long SESSION_TTL_SECONDS = 86400; // 1 day, match Python agent

    private final StringRedisTemplate redisTemplate;

    @Autowired
    public HistoryServiceImpl(StringRedisTemplate redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    @Override
    public List<SessionDTO> listSessions(Long userId) {
        // Scan Redis keys matching the user's sessions
        String pattern = HISTORY_KEY_PREFIX + "session-" + userId + "-*";
        Set<String> keys = redisTemplate.keys(pattern);

        if (keys == null || keys.isEmpty()) {
            return Collections.emptyList();
        }

        List<SessionDTO> sessions = new ArrayList<>();
        for (String key : keys) {
            String sessionId = key.substring(HISTORY_KEY_PREFIX.length());
            sessions.add(buildSessionDTO(sessionId));
        }

        // Sort by createdAt descending
        sessions.sort((a, b) -> Long.compare(b.getCreatedAt(), a.getCreatedAt()));
        return sessions;
    }

    @Override
    public List<Map<String, Object>> getSessionMessages(String sessionId) {
        String key = HISTORY_KEY_PREFIX + sessionId;
        String json = redisTemplate.opsForValue().get(key);
        if (json == null || json.isEmpty()) {
            return Collections.emptyList();
        }
        try {
            // JSONUtil.toList returns raw List, cast safely
            List<?> rawList = JSONUtil.toList(json, Map.class);
            List<Map<String, Object>> result = new ArrayList<>();
            for (Object item : rawList) {
                @SuppressWarnings("unchecked")
                Map<String, Object> map = (Map<String, Object>) item;
                result.add(map);
            }
            return result;
        } catch (Exception e) {
            return Collections.emptyList();
        }
    }

    @Override
    public void deleteSession(String sessionId) {
        String historyKey = HISTORY_KEY_PREFIX + sessionId;
        String metaKey = SESSION_META_PREFIX + sessionId;
        redisTemplate.delete(historyKey);
        redisTemplate.delete(metaKey);
    }

    @Override
    public void updateSessionTitle(String sessionId, String title) {
        String metaKey = SESSION_META_PREFIX + sessionId;
        redisTemplate.opsForHash().put(metaKey, "title", title);
        redisTemplate.opsForHash().put(metaKey, "updatedAt", String.valueOf(System.currentTimeMillis()));
        redisTemplate.expire(metaKey, SESSION_TTL_SECONDS, TimeUnit.SECONDS);
    }

    @Override
    public int getMessageCount(String sessionId) {
        List<Map<String, Object>> messages = getSessionMessages(sessionId);
        return messages.size();
    }

    /**
     * 构建会话 DTO，从 Redis 元数据 + 历史消息中提取信息
     */
    private SessionDTO buildSessionDTO(String sessionId) {
        // 1. Try to get stored metadata
        String metaKey = SESSION_META_PREFIX + sessionId;
        Map<Object, Object> meta = redisTemplate.opsForHash().entries(metaKey);

        String title = null;
        long createdAt;
        long updatedAt;

        if (meta.containsKey("title")) {
            title = (String) meta.get("title");
        }
        if (meta.containsKey("updatedAt")) {
            updatedAt = Long.parseLong((String) meta.get("updatedAt"));
        } else {
            updatedAt = extractTimestampFromSessionId(sessionId);
        }

        createdAt = extractTimestampFromSessionId(sessionId);

        // 2. Get messages to compute preview and count
        List<Map<String, Object>> messages = getSessionMessages(sessionId);
        int messageCount = messages.size();

        // 3. Generate preview from first user message
        String preview = null;
        if (title == null) {
            // Auto-generate title from first user message
            for (Map<String, Object> msg : messages) {
                if ("user".equals(msg.get("role"))) {
                    String content = (String) msg.get("content");
                    if (content != null) {
                        title = content.length() > 50 ? content.substring(0, 50) + "..." : content;
                        preview = content.length() > 100 ? content.substring(0, 100) + "..." : content;
                    }
                    break;
                }
            }
        } else {
            // preview from first user message
            for (Map<String, Object> msg : messages) {
                if ("user".equals(msg.get("role"))) {
                    String content = (String) msg.get("content");
                    if (content != null) {
                        preview = content.length() > 100 ? content.substring(0, 100) + "..." : content;
                    }
                    break;
                }
            }
        }

        if (title == null) {
            title = "新对话";
        }

        return SessionDTO.builder()
                .sessionId(sessionId)
                .title(title)
                .preview(preview)
                .createdAt(createdAt)
                .updatedAt(updatedAt)
                .messageCount(messageCount)
                .build();
    }

    /**
     * 从 sessionId 中提取时间戳：session-{userId}-{timestamp}-{random}
     */
    private long extractTimestampFromSessionId(String sessionId) {
        try {
            String[] parts = sessionId.split("-");
            if (parts.length >= 3) {
                return Long.parseLong(parts[2]);
            }
        } catch (NumberFormatException ignored) {
        }
        return System.currentTimeMillis();
    }
}
