package com.anxin_hitsz.service.plan;

import com.anxin_hitsz.dto.plan.PlanDTO;
import com.anxin_hitsz.dto.plan.PlanTaskDTO;
import com.anxin_hitsz.entity.Plan;
import com.baomidou.mybatisplus.extension.service.IService;

/**
 * ClassName: IPlanService
 * Package: com.anxin_hitsz.service.plan
 * Description: 计划服务接口
 *
 * @Author AnXin
 * @Create 2026/5/4
 * @Version 1.0
 */
public interface IPlanService extends IService<Plan> {

    /**
     * 创建新计划，包含根任务
     *
     * @param userId    用户 ID
     * @param sessionId 会话 ID
     * @param mainGoal  计划主要目标
     * @return 完整 PlanDTO（含任务树）
     * @throws RuntimeException 如果该会话已有计划
     */
    PlanDTO createPlan(Long userId, String sessionId, String mainGoal);

    /**
     * 根据会话 ID 获取计划
     *
     * @param sessionId 会话 ID
     * @return PlanDTO 或 null（不存在时）
     */
    PlanDTO getPlanBySessionId(String sessionId);

    /**
     * 添加子任务
     *
     * @param planId         计划 ID
     * @param parentTaskPath 父任务路径（如 "0"、"0.1"）
     * @param goal           子任务目标
     * @return 更新后的父任务 DTO（含子任务树）
     */
    PlanTaskDTO addSubtask(Long planId, String parentTaskPath, String goal);

    /**
     * 设置任务状态，并执行状态传播：
     * - COMPLETED/ABANDONED/VERIFIED → 递归设置所有子孙任务
     * - IN_PROGRESS → 递归设置所有祖先任务
     *
     * @param planId   计划 ID
     * @param taskPath 任务路径
     * @param state    新状态
     * @return 更新后的任务 DTO（含子任务树）
     */
    PlanTaskDTO setTaskState(Long planId, String taskPath, String state);

    /**
     * 删除计划及其所有任务（级联删除）
     */
    void deletePlan(Long planId);

    /**
     * 验证状态值是否合法
     */
    boolean isValidState(String state);
}
