package com.anxin_hitsz.controller.agent;

import com.anxin_hitsz.service.impl.user.account.UserDetailsImpl;
import com.anxin_hitsz.utils.Result;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;
import java.util.UUID;

/**
 * ClassName: SessionController
 * Package: com.anxin_hitsz.controller
 * Description: 对话 session 管理（由后端生成 sessionId，前端不参与）
 *
 * @Author AnXin
 * @Create 2026/5/2
 * @Version 1.0
 */
@RestController
@RequestMapping("/api/session")
public class SessionController {

    @PostMapping("/init")
    public Result init(Authentication authentication) {
        UserDetailsImpl loginUser = (UserDetailsImpl) authentication.getPrincipal();
        String sessionId = String.format(
                "session-%d-%d-%s",
                loginUser.getUser().getUserId(),
                System.currentTimeMillis(),
                UUID.randomUUID().toString().substring(0, 8)
        );
        return Result.ok(Map.of("sessionId", sessionId));
    }

    @PostMapping("/clear")
    public Result clear(Authentication authentication) {
        UserDetailsImpl loginUser = (UserDetailsImpl) authentication.getPrincipal();
        String sessionId = String.format(
                "session-%d-%d-%s",
                loginUser.getUser().getUserId(),
                System.currentTimeMillis(),
                UUID.randomUUID().toString().substring(0, 8)
        );
        return Result.ok(Map.of("sessionId", sessionId));
    }
}
