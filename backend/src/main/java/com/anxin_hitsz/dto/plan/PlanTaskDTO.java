package com.anxin_hitsz.dto.plan;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * ClassName: PlanTaskDTO
 * Package: com.anxin_hitsz.dto.plan
 * Description: 计划任务树节点 DTO，递归包含子任务
 *
 * @Author AnXin
 * @Create 2026/5/4
 * @Version 1.0
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class PlanTaskDTO {
    private Long taskId;
    private Long parentTaskId;
    private String taskPath;
    private String taskGoal;
    private String taskState;
    private Integer displayOrder;
    private List<PlanTaskDTO> subtasks;
}
