package com.anxin_hitsz.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * ClassName: Plan
 * Package: com.anxin_hitsz.entity
 * Description: 任务计划实体
 *
 * @Author AnXin
 * @Create 2026/5/4
 * @Version 1.0
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@TableName("tb_plan")
public class Plan {
    /**
     * 计划 ID
     */
    @TableId(type = IdType.AUTO)
    private Long planId;

    /**
     * 用户 ID
     */
    private Long userId;

    /**
     * 会话 ID
     */
    private String sessionId;

    /**
     * 计划主要目标
     */
    private String mainGoal;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;

    /**
     * 更新时间
     */
    private LocalDateTime updatedAt;
}
