"""
Plan 工具：供 LLM 调用的 CreatePlanTool / AddSubtaskTool / ModifyTaskTool
"""
from typing import Dict, Any, List

from app.tools.base import Tool, ToolParameter


class CreatePlanTool(Tool):
    """
    创建计划工具：为当前会话创建一个新的层级计划
    """

    def __init__(self, plan_manager):
        super().__init__(
            name="create_plan",
            description="为当前会话创建一个新的计划，包含主目标和根任务。每个会话只能有一个活动计划。"
        )
        self._plan_manager = plan_manager

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="main_goal",
                type="string",
                description="【必填】计划目标。调用示例: [TOOL_CALL:create_plan:{\"main_goal\": \"完成三篇技术文章\"}]",
                required=True,
            ),
        ]

    def run(self, parameters: Dict[str, Any]) -> str:
        # 兼容 LLM 常见的参数命名变体
        main_goal = (
            parameters.get("main_goal")
            or parameters.get("goal")
            or parameters.get("title")
            or ""
        ).strip()

        if not main_goal:
            return "错误：计划主目标（main_goal）不能为空。请使用 {\"main_goal\": \"你的计划目标\"} 格式。"

        return self._plan_manager.create_plan(main_goal)


class AddSubtaskTool(Tool):
    """
    添加子任务工具：为计划中的某个任务添加子任务
    """

    def __init__(self, plan_manager):
        super().__init__(
            name="add_subtask",
            description="为计划中的某个任务添加一个子任务。任务路径使用点分格式如 '0'（根任务）、'0.1'（第二个子任务）"
        )
        self._plan_manager = plan_manager

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="parent_task_path",
                type="string",
                description="父任务路径。调用示例: [TOOL_CALL:add_subtask:{\"parent_task_path\": \"0\", \"goal\": \"编写Redis文章\"}]",
                required=True,
            ),
            ToolParameter(
                name="goal",
                type="string",
                description="子任务的目标描述",
                required=True,
            ),
        ]

    def run(self, parameters: Dict[str, Any]) -> str:
        parent_task_path = (parameters.get("parent_task_path") or "").strip()
        goal = (parameters.get("goal") or "").strip()

        if not parent_task_path:
            return "错误：父任务路径不能为空"
        if not goal:
            return "错误：子任务目标不能为空"

        return self._plan_manager.add_subtask(parent_task_path, goal)


class ModifyTaskTool(Tool):
    """
    修改任务状态工具：更新计划中某个任务的状态（含状态传播）
    """

    def __init__(self, plan_manager):
        super().__init__(
            name="modify_task",
            description="修改计划中某个任务的状态。可选状态: open, in_progress, completed, verified, abandoned"
        )
        self._plan_manager = plan_manager

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="task_path",
                type="string",
                description="任务路径。调用示例: [TOOL_CALL:modify_task:{\"task_path\": \"0\", \"state\": \"completed\"}]",
                required=True,
            ),
            ToolParameter(
                name="state",
                type="string",
                description="目标状态：open（打开）, in_progress（进行中）, completed（已完成）, verified（已验证）, abandoned（已放弃）",
                required=True,
            ),
        ]

    def run(self, parameters: Dict[str, Any]) -> str:
        task_path = (parameters.get("task_path") or "").strip()
        state = (parameters.get("state") or "").strip()

        if not task_path:
            return "错误：任务路径不能为空"
        if not state:
            return "错误：状态不能为空"

        return self._plan_manager.set_task_state(task_path, state)
