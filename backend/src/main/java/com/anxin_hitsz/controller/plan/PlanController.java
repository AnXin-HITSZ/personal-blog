package com.anxin_hitsz.controller.plan;

import com.anxin_hitsz.dto.plan.PlanDTO;
import com.anxin_hitsz.dto.plan.PlanTaskDTO;
import com.anxin_hitsz.service.impl.user.account.UserDetailsImpl;
import com.anxin_hitsz.service.plan.IPlanService;
import com.anxin_hitsz.utils.Result;
import jakarta.annotation.Resource;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * ClassName: PlanController
 * Package: com.anxin_hitsz.controller.plan
 * Description: 任务计划管理控制器
 *
 * @Author AnXin
 * @Create 2026/5/4
 * @Version 1.0
 */
@RestController
@RequestMapping("/api/plan")
public class PlanController {

    @Resource
    private IPlanService planService;

    /**
     * 创建新计划
     * POST /api/plan/create
     * Body: { "sessionId": "...", "mainGoal": "...", "userId": 1 }
     *
     * userId 可选：前端调用时从 Authentication 提取，Agent 调用时从请求体获取
     */
    @PostMapping("/create")
    public Result createPlan(
            @RequestBody Map<String, String> body,
            Authentication authentication
    ) {
        Long userId = null;
        if (authentication != null && authentication.getPrincipal() instanceof UserDetailsImpl) {
            UserDetailsImpl loginUser = (UserDetailsImpl) authentication.getPrincipal();
            userId = loginUser.getUser().getUserId();
        }
        if (userId == null) {
            String userIdStr = body.get("userId");
            if (userIdStr != null) {
                try {
                    userId = Long.parseLong(userIdStr);
                } catch (NumberFormatException ignored) {}
            }
        }
        if (userId == null) {
            return Result.fail("无法获取用户 ID");
        }
        String sessionId = body.get("sessionId");
        String mainGoal = body.get("mainGoal");

        if (sessionId == null || sessionId.isBlank()) {
            return Result.fail("会话 ID 不能为空");
        }
        if (mainGoal == null || mainGoal.isBlank()) {
            return Result.fail("计划目标不能为空");
        }

        try {
            PlanDTO plan = planService.createPlan(userId, sessionId, mainGoal);
            return Result.ok(plan);
        } catch (RuntimeException e) {
            return Result.fail(e.getMessage());
        }
    }

    /**
     * 根据会话 ID 获取计划
     * GET /api/plan/{sessionId}
     */
    @GetMapping("/{sessionId}")
    public Result getPlan(@PathVariable String sessionId) {
        PlanDTO plan = planService.getPlanBySessionId(sessionId);
        if (plan == null) {
            return Result.fail("计划不存在");
        }
        return Result.ok(plan);
    }

    /**
     * 添加子任务
     * POST /api/plan/{planId}/task
     * Body: { "parentTaskPath": "0", "goal": "..." }
     */
    @PostMapping("/{planId}/task")
    public Result addTask(
            @PathVariable Long planId,
            @RequestBody Map<String, String> body
    ) {
        String parentTaskPath = body.get("parentTaskPath");
        String goal = body.get("goal");

        if (parentTaskPath == null || parentTaskPath.isBlank()) {
            return Result.fail("父任务路径不能为空");
        }
        if (goal == null || goal.isBlank()) {
            return Result.fail("任务目标不能为空");
        }

        try {
            PlanTaskDTO updated = planService.addSubtask(planId, parentTaskPath, goal);
            return Result.ok(updated);
        } catch (RuntimeException e) {
            return Result.fail(e.getMessage());
        }
    }

    /**
     * 设置任务状态
     * PUT /api/plan/{planId}/task/state
     * Body: { "taskPath": "0.1", "state": "completed" }
     */
    @PutMapping("/{planId}/task/state")
    public Result setTaskState(
            @PathVariable Long planId,
            @RequestBody Map<String, String> body
    ) {
        String taskPath = body.get("taskPath");
        String state = body.get("state");

        if (taskPath == null || taskPath.isBlank()) {
            return Result.fail("任务路径不能为空");
        }
        if (state == null || state.isBlank()) {
            return Result.fail("任务状态不能为空");
        }

        try {
            PlanTaskDTO updated = planService.setTaskState(planId, taskPath, state);
            return Result.ok(updated);
        } catch (RuntimeException e) {
            return Result.fail(e.getMessage());
        }
    }

    /**
     * 删除计划
     * DELETE /api/plan/{planId}
     */
    @DeleteMapping("/{planId}")
    public Result deletePlan(@PathVariable Long planId) {
        planService.deletePlan(planId);
        return Result.ok();
    }
}
