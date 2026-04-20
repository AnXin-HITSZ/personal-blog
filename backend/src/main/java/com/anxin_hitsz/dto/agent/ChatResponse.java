package com.anxin_hitsz.dto.agent;

import lombok.Data;

import java.util.Map;

/**
 * ClassName: ChatResponse
 * Package: com.anxin_hitsz.dto.agent
 * Description:
 *
 * @Author AnXin
 * @Create 2026/4/20 20:17
 * @Version 1.0
 */
@Data
public class ChatResponse {
    /**
     * LLM 返回文本内容
     */
    private String content;

    /**
     * 模型名称
     */
    private String model;

    /**
     * 消耗详情
     */
    private Map<String, Object> usage;

}
