package com.anxin_hitsz.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * ClassName: PlanTask
 * Package: com.anxin_hitsz.entity
 * Description: 计划任务实体
 *
 * @Author AnXin
 * @Create 2026/5/4
 * @Version 1.0
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@TableName("tb_plan_task")
public class PlanTask {
    /**
     * 任务 ID
     */
    @TableId(type = IdType.AUTO)
    private Long taskId;

    /**
     * 所属计划 ID
     */
    private Long planId;

    /**
     * 父任务 ID
     */
    private Long parentTaskId;

    /**
     * 任务路径：如 0、0.1、0.1.2
     */
    private String taskPath;

    /**
     * 任务目标描述
     */
    private String taskGoal;

    /**
     * 任务状态：open/in_progress/completed/verified/abandoned
     */
    private String taskState;

    /**
     * 显示顺序
     */
    private Integer displayOrder;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;

    /**
     * 更新时间
     */
    private LocalDateTime updatedAt;
}
