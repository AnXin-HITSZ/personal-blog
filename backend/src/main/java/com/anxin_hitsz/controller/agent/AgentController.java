package com.anxin_hitsz.controller.agent;

import com.anxin_hitsz.dto.agent.ChatRequest;
import com.anxin_hitsz.service.agent.IAgentService;
import com.anxin_hitsz.service.impl.user.account.UserDetailsImpl;
import jakarta.annotation.Resource;
import org.springframework.http.MediaType;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
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
     * 从认证上下文中提取 userId，覆盖客户端传入的 userId（防止越权）
     */
    private void enrichWithAuthenticatedUser(ChatRequest request) {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication != null && authentication.getPrincipal() instanceof UserDetailsImpl userDetails) {
            request.setUserId(userDetails.getUser().getUserId());
        }
    }

    /**
     * SimpleAgent - 流式响应
     */
    @PostMapping(value = "/chat/simple_agent/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter chatSimpleAgentStream(
            @RequestBody ChatRequest request
    ) {
        enrichWithAuthenticatedUser(request);
        return agentService.chatSimpleAgentStream(request);
    }

    /**
     * ReActAgent - 流式响应
     */
    @PostMapping(value = "/chat/react_agent/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter chatReActAgentStream(
            @RequestBody ChatRequest request
    ) {
        enrichWithAuthenticatedUser(request);
        return agentService.chatReActAgentStream(request);
    }
}
