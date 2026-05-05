"""
PlanManager：连接 Python Plan/Task 与 Java 后端 REST API
"""
import json
import os
import urllib.request
import urllib.error
from typing import Optional, List, Dict, Any

from app.plan.models import PlanDTO, TaskDTO, PlanEvent


BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8080")


class PlanManager:
    """
    计划管理器

    职责：
    1. 通过后端 REST API 持久化计划/任务
    2. 维护当前会话的 Plan 在内存中
    3. 缓存 SSE 事件供 ReActAgent 发送
    """

    def __init__(self, session_id: str, user_id: Optional[int] = None):
        self.session_id = session_id
        self.user_id = user_id
        self.current_plan: Optional["Plan"] = None  # type: ignore
        self._pending_events: List[Dict[str, Any]] = []

    # ---- SSE 事件管理 ----

    def pop_events(self) -> List[Dict[str, Any]]:
        """返回并清空待发送的 SSE 事件"""
        events = self._pending_events
        self._pending_events = []
        return events

    def _add_event(self, event_type: str, data: dict):
        """添加 SSE 事件到队列"""
        self._pending_events.append({"type": event_type, "data": data})

    # ---- 后端 API 调用 ----

    def load_from_backend(self) -> bool:
        """
        从后端加载当前会话的计划
        成功返回 True，无计划返回 False
        """
        if not self.session_id:
            return False

        url = f"{BACKEND_BASE_URL}/api/plan/{self.session_id}"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 500:
                # 后端返回 Result.fail("计划不存在") 也会导致 500
                # 这里我们通过读 body 来判断
                try:
                    err_body = json.loads(e.read().decode())
                    if not err_body.get("success"):
                        return False
                except Exception:
                    pass
            return False
        except Exception:
            return False

        if body.get("success") and body.get("data"):
            plan_dto = PlanDTO(**body["data"])
            from app.plan.plan import Plan
            self.current_plan = Plan.from_plan_dto(plan_dto)
            return True
        return False

    def create_plan(self, main_goal: str) -> str:
        """
        创建新计划

        POST /api/plan/create
        返回供 LLM 使用的描述文本
        """
        if self.current_plan is not None:
            return "当前会话已存在计划，请先完成或删除现有计划。"

        if self.user_id is None:
            return "错误：无法创建计划，缺少用户身份信息。当前会话未传递 user_id，请检查前端是否已登录并在 ChatRequest 中传入了 userId。"

        from app.plan.plan import Plan, Task

        # 先持久化到后端
        url = f"{BACKEND_BASE_URL}/api/plan/create"
        payload = json.dumps({
            "sessionId": self.session_id,
            "mainGoal": main_goal,
            "userId": str(self.user_id),
        }, ensure_ascii=False).encode("utf-8")

        try:
            req = urllib.request.Request(
                url, data=payload,
                headers={"Content-Type": "application/json; charset=utf-8"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            return f"创建计划失败 (HTTP {e.code}): {err_body}"
        except Exception as e:
            return f"创建计划失败: {str(e)}"

        if not body.get("success"):
            return f"创建计划失败: {body.get('errorMsg', '未知错误')}"

        # 从后端响应重建 Plan
        plan_dto = PlanDTO(**body["data"])
        self.current_plan = Plan.from_plan_dto(plan_dto)

        # 缓存 init SSE 事件
        self._add_event("plan_init", plan_dto.model_dump())

        task_tree = self.current_plan.task.to_string()
        return (
            f"✅ 计划创建成功！\n"
            f"主目标: {main_goal}\n\n"
            f"任务结构:\n{task_tree}\n"
            f"提示：根任务的路径为 0。添加子任务时请使用 parent_task_path=\"0\"。\n"
        )

    def add_subtask(self, parent_task_path: str, goal: str) -> str:
        """
        添加子任务

        POST /api/plan/{planId}/task
        返回供 LLM 使用的描述文本
        """
        if self.current_plan is None:
            return "错误：当前没有活动计划，请先创建计划。"

        plan_id = self.current_plan.plan_id
        if plan_id is None:
            return "错误：计划尚未持久化。"

        url = f"{BACKEND_BASE_URL}/api/plan/{plan_id}/task"
        payload = json.dumps({
            "parentTaskPath": parent_task_path,
            "goal": goal,
        }, ensure_ascii=False).encode("utf-8")

        try:
            req = urllib.request.Request(
                url, data=payload,
                headers={"Content-Type": "application/json; charset=utf-8"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            return f"添加子任务失败 (HTTP {e.code}): {err_body}"
        except Exception as e:
            return f"添加子任务失败: {str(e)}"

        if not body.get("success"):
            error_msg = body.get('errorMsg', '未知错误')
            # 父路径错误时给出提示
            if "父任务不存在" in error_msg:
                hint = "\n提示：根任务的路径为 0（如 parent_task_path=\"0\"），子任务路径格式为 0.1、0.2 等。请使用正确的任务路径重试。"
            else:
                hint = ""
            return f"添加子任务失败: {error_msg}{hint}"

        # 更新内存中的 Plan
        new_path = parent_task_path + "." + str(
            len(self.current_plan.get_task_by_id(parent_task_path).subtasks)
        )
        parent = self.current_plan.get_task_by_id(parent_task_path)
        from app.plan.plan import Task
        child = Task(parent=parent, goal=goal)
        parent.subtasks.append(child)

        # 缓存 SSE 事件
        updated_parent_dto = TaskDTO(**body["data"])
        self._add_event("plan_task_added", updated_parent_dto.model_dump())

        return (
            f"✅ 子任务添加成功！\n"
            f"任务路径: {new_path}\n"
            f"任务目标: {goal}\n"
            f"父任务: {parent_task_path}\n\n"
            f"当前工作流状态:\n{self.current_plan.task.to_string()}"
        )

    def set_task_state(self, task_path: str, state: str) -> str:
        """
        设置任务状态

        PUT /api/plan/{planId}/task/state
        返回供 LLM 使用的描述文本
        """
        from app.plan.models import STATES

        if state not in STATES:
            return f"错误：无效的状态 '{state}'。有效状态: {', '.join(STATES)}"

        if self.current_plan is None:
            return "错误：当前没有活动计划，请先创建计划。"

        plan_id = self.current_plan.plan_id
        if plan_id is None:
            return "错误：计划尚未持久化。"

        url = f"{BACKEND_BASE_URL}/api/plan/{plan_id}/task/state"
        payload = json.dumps({
            "taskPath": task_path,
            "state": state,
        }, ensure_ascii=False).encode("utf-8")

        try:
            req = urllib.request.Request(
                url, data=payload,
                headers={"Content-Type": "application/json; charset=utf-8"},
                method="PUT",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            return f"更新任务状态失败 (HTTP {e.code}): {err_body}"
        except Exception as e:
            return f"更新任务状态失败: {str(e)}"

        if not body.get("success"):
            return f"更新任务状态失败: {body.get('errorMsg', '未知错误')}"

        # 同步更新内存中的 Plan（含状态传播）—— 由后端完成传播后，我们直接重建
        from app.plan.plan import Plan
        plan_dto = PlanDTO(
            planId=self.current_plan.plan_id,
            mainGoal=self.current_plan.main_goal,
            sessionId=self.current_plan.session_id,
            userId=self.current_plan.user_id,
            rootTask=TaskDTO(**body["data"]),
        )
        # 仅更新目标任务及其子树
        updated_task_dto = TaskDTO(**body["data"])
        self._add_event("plan_task_update", updated_task_dto.model_dump())

        # 也更新内存中当前计划的状态
        try:
            target = self.current_plan.get_task_by_id(task_path)
            target.state = state
        except ValueError:
            pass

        # 状态传播由后端处理，我们在内存中简化处理
        if state in ("completed", "abandoned", "verified"):
            # 找到目标，递归设置子任务
            try:
                target = self.current_plan.get_task_by_id(task_path)
                target.state = state
                for sub in target.subtasks:
                    if sub.state != "abandoned":
                        sub.set_state(state)
            except ValueError:
                pass
        elif state == "in_progress":
            try:
                target = self.current_plan.get_task_by_id(task_path)
                target.state = state
                # 向上传播
                p = target.parent
                while p is not None:
                    p.state = state
                    p = p.parent
            except ValueError:
                pass

        return (
            f"✅ 任务状态已更新！\n"
            f"任务: {task_path}\n"
            f"新状态: {state}\n\n"
            f"当前工作流状态:\n{self.current_plan.task.to_string()}"
        )
