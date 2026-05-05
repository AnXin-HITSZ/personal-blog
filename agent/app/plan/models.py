"""
Plan/Task 相关数据模型与状态常量
"""

from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

# 任务状态常量（与 OpenDevin 一致）
OPEN_STATE = "open"
COMPLETED_STATE = "completed"
ABANDONED_STATE = "abandoned"
IN_PROGRESS_STATE = "in_progress"
VERIFIED_STATE = "verified"
STATES = [OPEN_STATE, COMPLETED_STATE, ABANDONED_STATE, IN_PROGRESS_STATE, VERIFIED_STATE]


class TaskDTO(BaseModel):
    """任务 DTO，用于后端 API 响应和 SSE 事件"""
    taskId: Optional[int] = None
    parentTaskId: Optional[int] = None
    taskPath: str
    taskGoal: str
    taskState: str = OPEN_STATE
    displayOrder: int = 0
    subtasks: List["TaskDTO"] = []


class PlanDTO(BaseModel):
    """计划 DTO，包含完整任务树"""
    planId: Optional[int] = None
    userId: Optional[int] = None
    sessionId: Optional[str] = None
    mainGoal: str
    rootTask: Optional[TaskDTO] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None


class PlanEvent(BaseModel):
    """SSE 事件负载，用于推送给前端"""
    type: str  # "plan_init" | "plan_task_added" | "plan_task_update"
    data: dict  # PlanDTO 或 TaskDTO 的 dict


# 修复 TaskDTO 的循环引用
TaskDTO.model_rebuild()
