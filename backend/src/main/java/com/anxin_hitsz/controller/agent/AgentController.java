package com.anxin_hitsz.controller.agent;

import com.anxin_hitsz.dto.agent.ChatRequest;
import com.anxin_hitsz.service.agent.IAgentService;
import com.anxin_hitsz.service.impl.user.account.UserDetailsImpl;
import jakarta.annotation.Resource;
import org.springframework.http.MediaType;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

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
     * SimpleAgent - 流式响应
     */
    @PostMapping(value = "/chat/simple_agent/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter chatSimpleAgentStream(
            @RequestBody ChatRequest request
    ) {
        return agentService.chatSimpleAgentStream(request);
    }

    /**
     * ReActAgent - 流式响应
     */
    @PostMapping(value = "/chat/react_agent/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter chatReActAgentStream(
            @RequestBody ChatRequest request
    ) {
        return agentService.chatReActAgentStream(request);
    }
}
