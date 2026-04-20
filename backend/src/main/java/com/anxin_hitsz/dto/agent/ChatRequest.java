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
     * 消息列表
     */
    private List<ChatMessage> messages;

    /**
     * 温度系数
     */
    private Double temperature = 0.7;

    /**
     * 是否开启流式响应
     */
    private Boolean isStream = true;

}
