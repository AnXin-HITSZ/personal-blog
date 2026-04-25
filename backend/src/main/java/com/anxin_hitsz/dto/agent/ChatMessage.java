package com.anxin_hitsz.dto.agent;

import lombok.Data;

/**
 * ClassName: ChatMessage
 * Package: com.anxin_hitsz.dto.agent
 * Description:
 *
 * @Author AnXin
 * @Create 2026/4/20 20:16
 * @Version 1.0
 */
@Data
public class ChatMessage {
    /**
     * 角色
     */
    private String role;

    /**
     * 输入 LLM 文本内容
     */
    private String content;

    /**
     * 时间戳
     */
    private Long timestamp;

}
