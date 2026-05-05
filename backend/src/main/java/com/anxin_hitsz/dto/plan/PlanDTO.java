package com.anxin_hitsz.dto.plan;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

/**
 * ClassName: PlanDTO
 * Package: com.anxin_hitsz.dto.plan
 * Description: 计划响应 DTO，包含完整任务树
 *
 * @Author AnXin
 * @Create 2026/5/4
 * @Version 1.0
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class PlanDTO {
    private Long planId;
    private Long userId;
    private String sessionId;
    private String mainGoal;
    private PlanTaskDTO rootTask;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
