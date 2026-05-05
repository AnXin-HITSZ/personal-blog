"""
从 OpenDevin 移植的 Plan/Task 数据结构和逻辑（plan.py）
"""
from typing import Optional, List, Dict, Any

from app.plan.models import (
    OPEN_STATE,
    COMPLETED_STATE,
    ABANDONED_STATE,
    IN_PROGRESS_STATE,
    VERIFIED_STATE,
    STATES,
    TaskDTO,
    PlanDTO,
)


class Task:
    """
    任务节点，构建层级任务树

    与 OpenDevin 的 Task 类保持行为一致：
    - 层级 ID 系统（"0", "0.1", "0.1.2"…）
    - 状态传播（完成→子任务完成，进行中→父任务进行中）
    - 当前任务查找（DFS 查找 IN_PROGRESS 任务）
    """

    def __init__(
        self,
        parent: Optional["Task"] = None,
        goal: str = "",
        state: str = OPEN_STATE,
        subtasks: Optional[List] = None,
        db_id: Optional[int] = None,
    ):
        if parent is None:
            self.id = "0"
        else:
            self.id = parent.id + "." + str(len(parent.subtasks))
        self.parent = parent
        self.goal = goal
        self.subtasks: List["Task"] = []
        for subtask in (subtasks or []):
            if isinstance(subtask, Task):
                self.subtasks.append(subtask)
            else:
                self.subtasks.append(Task(
                    parent=self,
                    goal=subtask.get("goal", ""),
                    state=subtask.get("state", OPEN_STATE),
                    subtasks=subtask.get("subtasks"),
                ))
        self.state = state
        self.db_id = db_id  # 后端数据库中的 taskId

    def to_string(self, indent: str = "") -> str:
        """返回任务及其子任务的格式化字符串（含 emoji）"""
        emoji = ""
        if self.state == VERIFIED_STATE:
            emoji = "✅"
        elif self.state == COMPLETED_STATE:
            emoji = "🟢"
        elif self.state == ABANDONED_STATE:
            emoji = "❌"
        elif self.state == IN_PROGRESS_STATE:
            emoji = "💪"
        elif self.state == OPEN_STATE:
            emoji = "🔵"
        result = indent + emoji + " " + self.id + " " + self.goal + "\n"
        for subtask in self.subtasks:
            result += subtask.to_string(indent + "    ")
        return result

    def to_dict(self) -> Dict[str, Any]:
        """返回任务的字典表示"""
        return {
            "id": self.id,
            "goal": self.goal,
            "state": self.state,
            "subtasks": [t.to_dict() for t in self.subtasks],
        }

    def to_task_dto(self) -> TaskDTO:
        """转换为 TaskDTO（给前端/API 使用）"""
        return TaskDTO(
            taskId=self.db_id,
            parentTaskId=self.parent.db_id if self.parent else None,
            taskPath=self.id,
            taskGoal=self.goal,
            taskState=self.state,
            displayOrder=0,
            subtasks=[st.to_task_dto() for st in self.subtasks],
        )

    @classmethod
    def from_task_dto(cls, dto: TaskDTO, parent: Optional["Task"] = None) -> "Task":
        """从 TaskDTO 重建任务树"""
        task = cls.__new__(cls)
        task.id = dto.taskPath
        task.parent = parent
        task.goal = dto.taskGoal
        task.state = dto.taskState
        task.db_id = dto.taskId
        task.subtasks = []
        for sub_dto in dto.subtasks:
            sub_task = cls.from_task_dto(sub_dto, parent=task)
            task.subtasks.append(sub_task)
        return task

    def set_state(self, state: str):
        """设置任务状态并传播

        与 OpenDevin 逻辑一致：
        - COMPLETED/ABANDONED/VERIFIED → 递归设置所有子孙任务
        - IN_PROGRESS → 递归设置所有祖先任务
        """
        if state not in STATES:
            raise ValueError(f"Invalid state: {state}")
        self.state = state
        if state in (COMPLETED_STATE, ABANDONED_STATE, VERIFIED_STATE):
            for subtask in self.subtasks:
                if subtask.state != ABANDONED_STATE:
                    subtask.set_state(state)
        elif state == IN_PROGRESS_STATE:
            if self.parent is not None:
                self.parent.set_state(state)

    def get_current_task(self) -> Optional["Task"]:
        """获取当前进行中的任务（DFS 遍历）"""
        for subtask in self.subtasks:
            if subtask.state == IN_PROGRESS_STATE:
                return subtask.get_current_task()
        if self.state == IN_PROGRESS_STATE:
            return self
        return None

    def get_task_by_id(self, task_id: str) -> Optional["Task"]:
        """根据路径 ID 查找任务，如 '0.1.2'"""
        try:
            parts = [int(p) for p in task_id.split(".")]
        except ValueError:
            return None
        if parts[0] != 0:
            return None
        parts = parts[1:]
        task = self
        for part in parts:
            if part >= len(task.subtasks):
                return None
            task = task.subtasks[part]
        return task

    def __str__(self) -> str:
        return f"Task(id={self.id}, goal={self.goal[:30] if self.goal else ''}..., state={self.state})"


class Plan:
    """
    计划，包含主目标和根任务树

    与 OpenDevin 的 Plan 类保持行为一致
    """

    def __init__(
        self,
        main_goal: str,
        plan_id: Optional[int] = None,
        session_id: Optional[str] = None,
        user_id: Optional[int] = None,
        root_task: Optional[Task] = None,
    ):
        self.plan_id = plan_id
        self.main_goal = main_goal
        self.session_id = session_id
        self.user_id = user_id
        self.task = root_task or Task(parent=None, goal=main_goal)

    def __str__(self) -> str:
        return self.task.to_string()

    def to_dict(self) -> Dict[str, Any]:
        """返回计划的字典表示"""
        return {
            "planId": self.plan_id,
            "mainGoal": self.main_goal,
            "sessionId": self.session_id,
            "userId": self.user_id,
            "rootTask": self.task.to_task_dto().model_dump(),
        }

    def to_plan_dto(self) -> PlanDTO:
        """转换为 PlanDTO"""
        return PlanDTO(
            planId=self.plan_id,
            sessionId=self.session_id,
            mainGoal=self.main_goal,
            userId=self.user_id,
            rootTask=self.task.to_task_dto(),
        )

    @classmethod
    def from_plan_dto(cls, dto: PlanDTO) -> "Plan":
        """从 PlanDTO 重建 Plan"""
        root_task = Task.from_task_dto(dto.rootTask) if dto.rootTask else None
        return cls(
            plan_id=dto.planId,
            main_goal=dto.mainGoal,
            session_id=dto.sessionId,
            user_id=dto.userId,
            root_task=root_task,
        )

    def get_task_by_id(self, task_id: str) -> Task:
        """根据路径 ID 获取任务"""
        task = self.task.get_task_by_id(task_id)
        if task is None:
            raise ValueError("Task does not exist: " + task_id)
        return task

    def add_subtask(self, parent_id: str, goal: str, subtasks: Optional[List] = None):
        """添加子任务"""
        parent = self.get_task_by_id(parent_id)
        child = Task(parent=parent, goal=goal, subtasks=subtasks or [])
        parent.subtasks.append(child)

    def set_subtask_state(self, task_id: str, state: str):
        """设置子任务状态"""
        task = self.get_task_by_id(task_id)
        task.set_state(state)

    def get_current_task(self) -> Optional[Task]:
        """获取当前进行中的任务"""
        return self.task.get_current_task()
