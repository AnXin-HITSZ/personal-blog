package com.anxin_hitsz.service.impl.agent;

import com.anxin_hitsz.dto.agent.ChatRequest;
import com.anxin_hitsz.service.agent.IAgentService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

/**
 * ClassName: AgentServiceImpl
 * Package: com.anxin_hitsz.service.impl.agent
 * Description:
 *
 * @Author AnXin
 * @Create 2026/4/20 20:26
 * @Version 1.0
 */
@Service
public class AgentServiceImpl implements IAgentService {

    private final WebClient webClient;

    @Autowired
    public AgentServiceImpl(WebClient webClient) {
        this.webClient = webClient;
    }

    @Override
    public SseEmitter chatSimpleAgentStream(ChatRequest request) {
        SseEmitter emitter = new SseEmitter(60 * 1000L);

        webClient.post()
                .uri("/api/agent/chat/simple_agent/stream")
                .bodyValue(request)
                .accept(MediaType.TEXT_PLAIN)
                .retrieve()
                .bodyToFlux(String.class)
                .subscribe(
                        chunk -> {
                            try {
                                emitter.send(chunk);
                            } catch (Exception e) {
                                emitter.completeWithError(e);
                            }
                        },
                        emitter::completeWithError,
                        emitter::complete
                );

        return emitter;
    }

    @Override
    public SseEmitter chatReActAgentStream(ChatRequest request) {
        SseEmitter emitter = new SseEmitter(60 * 1000L);

        webClient.post()
                .uri("/api/agent/chat/react_agent/stream")
                .bodyValue(request)
                .accept(MediaType.TEXT_PLAIN)
                .retrieve()
                .bodyToFlux(String.class)
                .subscribe(
                        chunk -> {
                            try {
                                emitter.send(chunk);
                            } catch (Exception e) {
                                emitter.completeWithError(e);
                            }
                        },
                        emitter::completeWithError,
                        emitter::complete
                );

        return emitter;
    }
}
