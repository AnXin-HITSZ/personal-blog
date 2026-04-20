package com.anxin_hitsz.service.agent;

import com.anxin_hitsz.dto.agent.ChatRequest;
import com.anxin_hitsz.dto.agent.ChatResponse;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

/**
 * ClassName: IAgentService
 * Package: com.anxin_hitsz.service.agent
 * Description:
 *
 * @Author AnXin
 * @Create 2026/4/20 20:25
 * @Version 1.0
 */
public interface IAgentService {
    SseEmitter streamChat(ChatRequest chatRequest);
}
