package com.anxin_hitsz.controller.agent;

import com.anxin_hitsz.dto.agent.ChatRequest;
import com.anxin_hitsz.dto.agent.ChatResponse;
import com.anxin_hitsz.service.agent.IAgentService;
import jakarta.annotation.Resource;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.awt.*;

/**
 * ClassName: AgentController
 * Package: com.anxin_hitsz.controller.agent
 * Description:
 *
 * @Author AnXin
 * @Create 2026/4/20 20:23
 * @Version 1.0
 */
@RestController
@RequestMapping("/api/agent")
public class AgentController {

    @Resource
    private IAgentService agentService;

    /**
     * 与 LLM 日常交流 - 流式响应
     */
    @PostMapping(value = "/chat", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter chat(@RequestBody ChatRequest request) {
        return agentService.streamChat(request);
    }
}
