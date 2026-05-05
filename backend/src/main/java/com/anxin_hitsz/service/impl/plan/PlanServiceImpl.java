package com.anxin_hitsz.service.impl.plan;

import com.anxin_hitsz.dto.plan.PlanDTO;
import com.anxin_hitsz.dto.plan.PlanTaskDTO;
import com.anxin_hitsz.entity.Plan;
import com.anxin_hitsz.entity.PlanTask;
import com.anxin_hitsz.mapper.plan.PlanMapper;
import com.anxin_hitsz.mapper.plan.PlanTaskMapper;
import com.anxin_hitsz.service.plan.IPlanService;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import jakarta.annotation.Resource;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

/**
 * ClassName: PlanServiceImpl
 * Package: com.anxin_hitsz.service.impl.plan
 * Description: 计划服务实现，包含任务树构建与状态传播
 *
 * @Author AnXin
 * @Create 2026/5/4
 * @Version 1.0
 */
@Service
public class PlanServiceImpl extends ServiceImpl<PlanMapper, Plan> implements IPlanService {

    private static final String OPEN_STATE = "open";
    private static final String COMPLETED_STATE = "completed";
    private static final String ABANDONED_STATE = "abandoned";
    private static final String IN_PROGRESS_STATE = "in_progress";
    private static final String VERIFIED_STATE = "verified";
    private static final Set<String> STATES = Set.of(
            OPEN_STATE, COMPLETED_STATE, ABANDONED_STATE, IN_PROGRESS_STATE, VERIFIED_STATE
    );

    @Resource
    private PlanTaskMapper planTaskMapper;

    @Override
    @Transactional
    public PlanDTO createPlan(Long userId, String sessionId, String mainGoal) {
        // 检查会话是否已有计划
        Plan existing = lambdaQuery().eq(Plan::getSessionId, sessionId).one();
        if (existing != null) {
            throw new RuntimeException("该会话已存在计划");
        }

        // 创建计划
        Plan plan = new Plan();
        plan.setUserId(userId);
        plan.setSessionId(sessionId);
        plan.setMainGoal(mainGoal);
        plan.setCreatedAt(LocalDateTime.now());
        plan.setUpdatedAt(LocalDateTime.now());
        save(plan);

        // 创建根任务（taskPath = "0"）
        PlanTask rootTask = new PlanTask();
        rootTask.setPlanId(plan.getPlanId());
        rootTask.setParentTaskId(null);
        rootTask.setTaskPath("0");
        rootTask.setTaskGoal(mainGoal);
        rootTask.setTaskState(IN_PROGRESS_STATE);
        rootTask.setDisplayOrder(0);
        rootTask.setCreatedAt(LocalDateTime.now());
        rootTask.setUpdatedAt(LocalDateTime.now());
        planTaskMapper.insert(rootTask);

        return buildPlanDTO(plan);
    }

    @Override
    public PlanDTO getPlanBySessionId(String sessionId) {
        Plan plan = lambdaQuery().eq(Plan::getSessionId, sessionId).one();
        if (plan == null) {
            return null;
        }
        return buildPlanDTO(plan);
    }

    @Override
    @Transactional
    public PlanTaskDTO addSubtask(Long planId, String parentTaskPath, String goal) {
        // 查找父任务
        PlanTask parent = findTaskByPath(planId, parentTaskPath);
        if (parent == null) {
            throw new RuntimeException("父任务不存在: " + parentTaskPath);
        }

        // 计算同级子任务数量，确定新路径
        Long siblingCount = planTaskMapper.selectCount(
                new QueryWrapper<PlanTask>()
                        .eq("plan_id", planId)
                        .eq("parent_task_id", parent.getTaskId())
        );
        String newPath = parentTaskPath + "." + siblingCount;

        // 创建子任务
        PlanTask task = new PlanTask();
        task.setPlanId(planId);
        task.setParentTaskId(parent.getTaskId());
        task.setTaskPath(newPath);
        task.setTaskGoal(goal);
        task.setTaskState(OPEN_STATE);
        task.setDisplayOrder(siblingCount.intValue());
        task.setCreatedAt(LocalDateTime.now());
        task.setUpdatedAt(LocalDateTime.now());
        planTaskMapper.insert(task);

        // 返回更新后的父任务（含子任务树）
        return buildTaskDTO(planId, parent.getTaskId());
    }

    @Override
    @Transactional
    public PlanTaskDTO setTaskState(Long planId, String taskPath, String state) {
        if (!isValidState(state)) {
            throw new RuntimeException("无效的任务状态: " + state);
        }

        PlanTask target = findTaskByPath(planId, taskPath);
        if (target == null) {
            throw new RuntimeException("任务不存在: " + taskPath);
        }

        // 加载该计划的所有任务到内存
        List<PlanTask> allTasks = planTaskMapper.selectList(
                new QueryWrapper<PlanTask>().eq("plan_id", planId)
        );

        // 构建父子映射
        Map<Long, List<PlanTask>> parentToChildren = allTasks.stream()
                .filter(t -> t.getParentTaskId() != null)
                .collect(Collectors.groupingBy(PlanTask::getParentTaskId));

        Map<Long, PlanTask> idToTask = allTasks.stream()
                .collect(Collectors.toMap(PlanTask::getTaskId, t -> t));

        // 更新目标任务状态
        target.setTaskState(state);
        target.setUpdatedAt(LocalDateTime.now());

        // 执行状态传播
        Set<Long> changedIds = new HashSet<>();
        if (COMPLETED_STATE.equals(state) || ABANDONED_STATE.equals(state) || VERIFIED_STATE.equals(state)) {
            // 向下传播：递归设置所有子孙任务
            propagateStateDownwards(target.getTaskId(), state, parentToChildren, idToTask, changedIds);
        } else if (IN_PROGRESS_STATE.equals(state)) {
            // 向上传播：递归设置所有祖先任务
            propagateStateUpwards(target, state, idToTask, changedIds);
        }

        // 批量更新到数据库
        changedIds.add(target.getTaskId());
        for (Long tid : changedIds) {
            PlanTask t = idToTask.get(tid);
            t.setUpdatedAt(LocalDateTime.now());
            planTaskMapper.updateById(t);
        }

        // 返回更新后的任务（含子任务树）
        return buildTaskDTO(planId, target.getTaskId());
    }

    @Override
    @Transactional
    public void deletePlan(Long planId) {
        // 外键级联删除会自动删除所有任务
        removeById(planId);
    }

    @Override
    public boolean isValidState(String state) {
        return state != null && STATES.contains(state);
    }

    // ========================
    // 内部工具方法
    // ========================

    /**
     * 根据 planId + taskPath 查找任务
     */
    private PlanTask findTaskByPath(Long planId, String taskPath) {
        return planTaskMapper.selectOne(
                new QueryWrapper<PlanTask>()
                        .eq("plan_id", planId)
                        .eq("task_path", taskPath)
        );
    }

    /**
     * 构建完整的 PlanDTO（含任务树）
     */
    private PlanDTO buildPlanDTO(Plan plan) {
        PlanTaskDTO rootTask = buildTaskDTO(plan.getPlanId(), null);
        return new PlanDTO(
                plan.getPlanId(),
                plan.getUserId(),
                plan.getSessionId(),
                plan.getMainGoal(),
                rootTask,
                plan.getCreatedAt(),
                plan.getUpdatedAt()
        );
    }

    /**
     * 递归构建任务树 DTO
     *
     * @param planId       计划 ID
     * @param parentTaskId 父任务 ID，null 表示从根任务开始构建
     */
    private PlanTaskDTO buildTaskDTO(Long planId, Long parentTaskId) {
        PlanTask task;
        if (parentTaskId == null) {
            // 查找根任务（taskPath = "0"）
            task = planTaskMapper.selectOne(
                    new QueryWrapper<PlanTask>()
                            .eq("plan_id", planId)
                            .eq("task_path", "0")
            );
        } else {
            task = planTaskMapper.selectById(parentTaskId);
        }

        if (task == null) {
            return null;
        }

        // 递归构建子任务
        List<PlanTaskDTO> subDTOs = buildChildTaskDTOs(planId, task.getTaskId());

        return new PlanTaskDTO(
                task.getTaskId(),
                task.getParentTaskId(),
                task.getTaskPath(),
                task.getTaskGoal(),
                task.getTaskState(),
                task.getDisplayOrder(),
                subDTOs
        );
    }

    /**
     * 构建指定父任务的所有子任务的 DTO 列表（递归）
     */
    private List<PlanTaskDTO> buildChildTaskDTOs(Long planId, Long parentTaskId) {
        QueryWrapper<PlanTask> wrapper = new QueryWrapper<PlanTask>()
                .eq("plan_id", planId)
                .eq("parent_task_id", parentTaskId)
                .orderByAsc("display_order");

        List<PlanTask> children = planTaskMapper.selectList(wrapper);
        List<PlanTaskDTO> result = new ArrayList<>();

        for (PlanTask child : children) {
            List<PlanTaskDTO> grandchildren = buildChildTaskDTOs(planId, child.getTaskId());
            result.add(new PlanTaskDTO(
                    child.getTaskId(),
                    child.getParentTaskId(),
                    child.getTaskPath(),
                    child.getTaskGoal(),
                    child.getTaskState(),
                    child.getDisplayOrder(),
                    grandchildren
            ));
        }

        return result;
    }

    /**
     * 向下传播状态：将目标任务的 state 递归设置到所有子孙任务
     */
    private void propagateStateDownwards(
            Long parentId, String state,
            Map<Long, List<PlanTask>> parentToChildren,
            Map<Long, PlanTask> idToTask,
            Set<Long> changedIds
    ) {
        List<PlanTask> children = parentToChildren.get(parentId);
        if (children == null) return;

        for (PlanTask child : children) {
            if (ABANDONED_STATE.equals(child.getTaskState())) {
                // 已放弃的任务不改变状态
                continue;
            }
            child.setTaskState(state);
            changedIds.add(child.getTaskId());
            propagateStateDownwards(child.getTaskId(), state, parentToChildren, idToTask, changedIds);
        }
    }

    /**
     * 向上传播状态：将目标任务的状态递归设置到所有祖先任务
     */
    private void propagateStateUpwards(
            PlanTask task, String state,
            Map<Long, PlanTask> idToTask,
            Set<Long> changedIds
    ) {
        if (task.getParentTaskId() == null) return;

        PlanTask parent = idToTask.get(task.getParentTaskId());
        if (parent == null) return;

        parent.setTaskState(state);
        changedIds.add(parent.getTaskId());
        propagateStateUpwards(parent, state, idToTask, changedIds);
    }
}
