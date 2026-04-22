package com.anxin_hitsz.dto.agent;

import lombok.Data;

import java.util.List;

/**
 * ClassName: ChatRequest
 * Package: com.anxin_hitsz.dto.agent
 * Description:
 *
 * @Author AnXin
 * @Create 2026/4/20 20:15
 * @Version 1.0
 */
@Data
public class ChatRequest {
    /**
     * 用户历史消息记录 Redis id
     */
    private String sessionId;

    /**
     * 消息列表
     */
    private List<ChatMessage> messages;

    /**
     * 是否开启流式响应
     */
    private Boolean stream = true;

}
