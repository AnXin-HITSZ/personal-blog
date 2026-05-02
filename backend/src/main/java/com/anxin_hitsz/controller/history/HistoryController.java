package com.anxin_hitsz.controller.history;

import com.anxin_hitsz.dto.history.SessionDTO;
import com.anxin_hitsz.service.history.IHistoryService;
import com.anxin_hitsz.service.impl.user.account.UserDetailsImpl;
import com.anxin_hitsz.utils.Result;
import jakarta.annotation.Resource;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * ClassName: HistoryController
 * Package: com.anxin_hitsz.controller.history
 * Description: 对话历史管理（列表、查看、删除、重命名）
 *
 * @Author AnXin
 * @Create 2026/5/2
 * @Version 1.0
 */
@RestController
@RequestMapping("/api/history")
public class HistoryController {

    @Resource
    private IHistoryService historyService;

    /**
     * 获取当前用户的所有历史会话
     */
    @GetMapping("/list")
    public Result listSessions(Authentication authentication) {
        UserDetailsImpl loginUser = (UserDetailsImpl) authentication.getPrincipal();
        Long userId = loginUser.getUser().getUserId();
        List<SessionDTO> sessions = historyService.listSessions(userId);
        return Result.ok(sessions);
    }

    /**
     * 获取指定会话的消息内容
     */
    @GetMapping("/{sessionId}")
    public Result getSessionMessages(@PathVariable String sessionId) {
        List<Map<String, Object>> messages = historyService.getSessionMessages(sessionId);
        return Result.ok(messages);
    }

    /**
     * 删除指定会话
     */
    @DeleteMapping("/{sessionId}")
    public Result deleteSession(@PathVariable String sessionId) {
        historyService.deleteSession(sessionId);
        return Result.ok();
    }

    /**
     * 更新会话标题
     */
    @PutMapping("/{sessionId}/title")
    public Result updateSessionTitle(
            @PathVariable String sessionId,
            @RequestBody Map<String, String> body
    ) {
        String title = body.get("title");
        if (title == null || title.isBlank()) {
            return Result.fail("标题不能为空");
        }
        historyService.updateSessionTitle(sessionId, title.trim());
        return Result.ok();
    }
}
