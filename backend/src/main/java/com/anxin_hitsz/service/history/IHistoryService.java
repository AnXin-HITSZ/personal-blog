package com.anxin_hitsz.service.history;

import com.anxin_hitsz.dto.history.SessionDTO;

import java.util.List;
import java.util.Map;

/**
 * ClassName: IHistoryService
 * Package: com.anxin_hitsz.service.history
 * Description: 对话历史服务接口
 *
 * @Author AnXin
 * @Create 2026/5/2
 * @Version 1.0
 */
public interface IHistoryService {

    /**
     * 获取用户的所有历史会话
     */
    List<SessionDTO> listSessions(Long userId);

    /**
     * 获取指定会话的消息列表
     */
    List<Map<String, Object>> getSessionMessages(String sessionId);

    /**
     * 删除指定会话
     */
    void deleteSession(String sessionId);

    /**
     * 更新会话标题
     */
    void updateSessionTitle(String sessionId, String title);

    /**
     * 获取会话消息条数
     */
    int getMessageCount(String sessionId);
}
