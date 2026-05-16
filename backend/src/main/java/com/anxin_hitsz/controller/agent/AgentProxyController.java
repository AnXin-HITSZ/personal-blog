package com.anxin_hitsz.controller.agent;

import com.anxin_hitsz.utils.Result;
import cn.hutool.json.JSONUtil;
import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestClient;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;

import org.springframework.security.core.context.SecurityContext;
import org.springframework.security.core.context.SecurityContextHolder;

/**
 * Agent 代理控制器
 * <p>
 * 接收前端发来的 Agent 请求，在 JWT 认证通过后转发给 FastAPI 服务。
 */
@RestController
@RequestMapping("/api/agent")
public class AgentProxyController {

    @Value("${fastapi.service.url}")
    private String fastApiBaseUrl;

    @Value("${fastapi.service.timeout:60000}")
    private long timeout;

    private RestClient restClient;
    private final HttpClient streamingHttpClient = HttpClient.newHttpClient();

    @PostConstruct
    public void init() {
        this.restClient = RestClient.builder()
                .baseUrl(fastApiBaseUrl)
                .build();
    }

    // ──────────── RAG 搜索 ────────────

    @PostMapping("/rag/search")
    public Result ragSearch(@RequestBody Map<String, Object> request) {
        return proxyPost("/api/agent/rag/search", request);
    }

    @GetMapping("/rag/stats")
    public Result ragStats() {
        return proxyGet("/api/agent/rag/stats");
    }

    // ──────────── 文件上传与知识库 ────────────

    /**
     * 上传文件并自动索引到知识库
     */
    @PostMapping(value = "/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public Result uploadFile(@RequestParam("file") MultipartFile file) {
        try {
            ByteArrayResource resource = new ByteArrayResource(file.getBytes()) {
                @Override
                public String getFilename() {
                    return file.getOriginalFilename();
                }
            };

            MultiValueMap<String, Object> formData = new LinkedMultiValueMap<>();
            formData.add("file", resource);

            ResponseEntity<Map> response = restClient.post()
                    .uri("/api/agent/upload")
                    .body(formData)
                    .retrieve()
                    .toEntity(Map.class);

            Map<String, Object> body = response.getBody();
            return body != null ? Result.ok(body) : Result.fail("文件上传失败");
        } catch (Exception e) {
            return Result.fail("文件上传失败: " + e.getMessage());
        }
    }

    /**
     * 获取知识库文件列表
     */
    @GetMapping("/files")
    public Result listFiles(@RequestParam(value = "ext", required = false) String ext) {
        try {
            ResponseEntity<Map> response;
            if (ext != null && !ext.isBlank()) {
                response = restClient.get()
                        .uri("/api/agent/files?ext={ext}", ext)
                        .retrieve()
                        .toEntity(Map.class);
            } else {
                response = restClient.get()
                        .uri("/api/agent/files")
                        .retrieve()
                        .toEntity(Map.class);
            }

            Map<String, Object> body = response.getBody();
            return body != null ? Result.ok(body) : Result.fail("获取文件列表失败");
        } catch (Exception e) {
            return Result.fail("获取文件列表失败: " + e.getMessage());
        }
    }

    /**
     * 删除知识库中的文件索引
     */
    @DeleteMapping("/rag/source")
    public Result deleteSource(@RequestParam("file_path") String filePath) {
        try {
            ResponseEntity<Map> response = restClient.delete()
                    .uri("/api/agent/rag/source?file_path={filePath}", filePath)
                    .retrieve()
                    .toEntity(Map.class);

            Map<String, Object> body = response.getBody();
            return body != null ? Result.ok(body) : Result.fail("删除索引失败");
        } catch (Exception e) {
            return Result.fail("删除索引失败: " + e.getMessage());
        }
    }

    /**
     * 索引知识库目录
     */
    @PostMapping("/index_directory")
    public Result indexDirectory(@RequestBody Map<String, Object> request) {
        return proxyPost("/api/agent/index_directory", request);
    }

    // ──────────── Skill 管理 ────────────

    @GetMapping("/skills")
    public Result listSkills() {
        return proxyGet("/api/agent/skills");
    }

    @PostMapping("/skills/configure")
    public Result configureSkills(@RequestBody Map<String, Object> request) {
        return proxyPost("/api/agent/skills/configure", request);
    }

    // ──────────── 健康检查 ────────────

    @GetMapping("/health")
    public Result health() {
        return proxyGet("/api/agent/health");
    }

    // ──────────── 部署管理 ────────────

    @PostMapping("/deploy/trigger")
    public Result deployTrigger(@RequestBody Map<String, Object> request) {
        try {
            ResponseEntity<Map> response = restClient.post()
                    .uri("/api/agent/deploy/trigger")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(request)
                    .retrieve()
                    .toEntity(Map.class);

            Map<String, Object> body = response.getBody();
            if (body == null) {
                return Result.fail("Agent 服务返回空响应");
            }

            // Agent 返回 { message, branch }，直接返回给前端
            return Result.ok(body);
        } catch (Exception e) {
            return Result.fail("触发部署失败: " + e.getMessage());
        }
    }

    @GetMapping("/deploy/history")
    public Result deployHistory(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int size
    ) {
        try {
            ResponseEntity<Map> response = restClient.get()
                    .uri("/api/agent/deploy/history?page={page}&size={size}", page, size)
                    .retrieve()
                    .toEntity(Map.class);

            Map<String, Object> body = response.getBody();
            if (body != null && Integer.valueOf(200).equals(body.get("code"))) {
                return Result.ok(body.get("data"));
            }
            return Result.fail(body != null ? (String) body.get("message") : "获取部署历史失败");
        } catch (Exception e) {
            return Result.fail("获取部署历史失败: " + e.getMessage());
        }
    }

    @GetMapping("/deploy/{deploymentId}")
    public Result deployDetail(@PathVariable String deploymentId) {
        try {
            ResponseEntity<Map> response = restClient.get()
                    .uri("/api/agent/deploy/{deploymentId}", deploymentId)
                    .retrieve()
                    .toEntity(Map.class);

            Map<String, Object> body = response.getBody();
            if (body != null && Integer.valueOf(200).equals(body.get("code"))) {
                return Result.ok(body.get("data"));
            }
            return Result.fail(body != null ? (String) body.get("message") : "获取部署详情失败");
        } catch (Exception e) {
            return Result.fail("获取部署详情失败: " + e.getMessage());
        }
    }

    @PostMapping("/deploy/{deploymentId}/cancel")
    public Result cancelDeploy(@PathVariable String deploymentId) {
        try {
            ResponseEntity<Map> response = restClient.post()
                    .uri("/api/agent/deploy/{deploymentId}/cancel", deploymentId)
                    .retrieve()
                    .toEntity(Map.class);

            Map<String, Object> body = response.getBody();
            if (body != null && Integer.valueOf(200).equals(body.get("code"))) {
                return Result.ok(body.get("data"));
            }
            return Result.fail(body != null ? (String) body.get("message") : "取消部署失败");
        } catch (Exception e) {
            return Result.fail("取消部署失败: " + e.getMessage());
        }
    }

    // ──────────── 非流式对话 ────────────

    @PostMapping("/chat")
    public Result chat(@RequestBody Map<String, Object> request) {
        try {
            String question = (String) request.get("question");
            String sessionId = (String) request.getOrDefault("sessionId", UUID.randomUUID().toString());

            Map<String, Object> agentReq = new HashMap<>();
            agentReq.put("Id", sessionId);
            agentReq.put("Question", question);

            ResponseEntity<Map> response = restClient.post()
                    .uri("/api/agent/chat")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(agentReq)
                    .retrieve()
                    .toEntity(Map.class);

            Map<String, Object> body = response.getBody();
            if (body == null) {
                return Result.fail("Agent 服务返回空响应");
            }

            // FastAPI 返回 { code, message, data: { success, answer, errorMessage } }
            return Result.ok(body);
        } catch (Exception e) {
            return Result.fail("Agent 对话调用失败: " + e.getMessage());
        }
    }

    // ──────────── 流式对话 (SSE) ────────────

    @PostMapping("/chat/stream")
    public SseEmitter chatStream(@RequestBody Map<String, Object> request) {
        String question = (String) request.get("question");
        String sessionId = (String) request.getOrDefault("sessionId", UUID.randomUUID().toString());

        SseEmitter emitter = new SseEmitter(180_000L);

        Map<String, Object> agentReq = new HashMap<>();
        agentReq.put("Id", sessionId);
        agentReq.put("Question", question);

        SecurityContext securityContext = SecurityContextHolder.getContext();

        CompletableFuture.runAsync(() -> {
            SecurityContextHolder.setContext(securityContext);
            try {
                // 使用 Java HttpClient + BodyHandlers.ofInputStream() 实现真正流式转发
                String jsonBody = JSONUtil.toJsonStr(agentReq);
                HttpRequest httpRequest = HttpRequest.newBuilder()
                        .uri(URI.create(fastApiBaseUrl + "/api/agent/chat_stream"))
                        .header("Content-Type", "application/json")
                        .POST(HttpRequest.BodyPublishers.ofString(jsonBody))
                        .build();

                HttpResponse<java.io.InputStream> httpResponse = streamingHttpClient.send(
                        httpRequest, HttpResponse.BodyHandlers.ofInputStream());

                try (BufferedReader reader = new BufferedReader(
                        new InputStreamReader(httpResponse.body(), StandardCharsets.UTF_8))) {
                    String line;
                    while ((line = reader.readLine()) != null) {
                        if (line.startsWith("data: ")) {
                            String jsonData = line.substring(6);
                            emitter.send(SseEmitter.event()
                                    .name("message")
                                    .data(jsonData));
                        }
                    }
                }
                emitter.complete();
            } catch (Exception e) {
                try {
                    emitter.send(SseEmitter.event()
                            .name("message")
                            .data("{\"type\":\"error\",\"data\":\"" +
                                    e.getMessage().replace("\"", "\\\"") + "\"}"));
                } catch (Exception ignored) {
                }
                emitter.complete();
            } finally {
                SecurityContextHolder.clearContext();
            }
        });

        return emitter;
    }

    // ──────────── 会话管理 ────────────

    @PostMapping("/chat/clear")
    public Result clearSession(@RequestBody Map<String, Object> request) {
        try {
            String sessionId = (String) request.get("sessionId");

            Map<String, Object> agentReq = new HashMap<>();
            agentReq.put("sessionId", sessionId);

            ResponseEntity<Map> response = restClient.post()
                    .uri("/api/agent/chat/clear")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(agentReq)
                    .retrieve()
                    .toEntity(Map.class);

            Map<String, Object> body = response.getBody();
            return body != null ? Result.ok(body) : Result.fail("清空会话失败");
        } catch (Exception e) {
            return Result.fail("清空会话失败: " + e.getMessage());
        }
    }

    @GetMapping("/chat/session/{sessionId}")
    public Result getSessionInfo(@PathVariable String sessionId) {
        return proxyGet("/api/agent/chat/session/" + sessionId);
    }

    @GetMapping("/chat/sessions")
    public Result listSessions() {
        return proxyGet("/api/agent/chat/sessions");
    }

    @DeleteMapping("/chat/session/{sessionId}")
    public Result deleteSession(@PathVariable String sessionId) {
        try {
            ResponseEntity<Map> response = restClient.delete()
                    .uri("/api/agent/chat/session/{sessionId}", sessionId)
                    .retrieve()
                    .toEntity(Map.class);

            Map<String, Object> body = response.getBody();
            return body != null ? Result.ok(body) : Result.fail("删除会话失败");
        } catch (Exception e) {
            return Result.fail("删除会话失败: " + e.getMessage());
        }
    }

    // ──────────── 通用代理方法 ────────────

    private Result proxyPost(String path, Object body) {
        try {
            ResponseEntity<Map> response = restClient.post()
                    .uri(path)
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(body)
                    .retrieve()
                    .toEntity(Map.class);

            Map<String, Object> responseBody = response.getBody();
            if (responseBody == null) {
                return Result.fail("Agent 服务返回空响应");
            }

            return Result.ok(responseBody);
        } catch (Exception e) {
            return Result.fail("Agent 服务调用失败: " + e.getMessage());
        }
    }

    private Result proxyGet(String path) {
        try {
            ResponseEntity<Map> response = restClient.get()
                    .uri(path)
                    .retrieve()
                    .toEntity(Map.class);

            Map<String, Object> responseBody = response.getBody();
            if (responseBody == null) {
                return Result.fail("Agent 服务返回空响应");
            }

            return Result.ok(responseBody);
        } catch (Exception e) {
            return Result.fail("Agent 服务调用失败: " + e.getMessage());
        }
    }
}
