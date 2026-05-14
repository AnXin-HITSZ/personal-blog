"""部署服务 — 编排部署流水线的执行与事件流"""

import uuid
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, Optional

from loguru import logger

from app.config import config
from app.agent.deploy.graph import build_deployment_graph
from app.agent.deploy.state import DeploymentState
from app.services.deployment_memory import deployment_memory

# 部署阶段显示名称
PHASE_NAMES = {
    "trigger": "触发更新",
    "code_prepare": "代码准备",
    "build_test": "构建测试",
    "deploy": "部署发布",
    "verify": "全面验证",
    "complete": "完成收尾",
    "rollback": "智能回滚",
}


class DeploymentService:
    """部署服务 — 编排 LangGraph 部署流水线"""

    def __init__(self):
        self.graph = build_deployment_graph()
        logger.info("DeploymentService 初始化完成")

    async def execute(
        self,
        trigger_type: str,
        trigger_data: Optional[Dict[str, Any]] = None,
        branch: str = "main",
        deployment_id: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """执行部署流水线

        Args:
            trigger_type: 触发方式 (webhook/manual)
            trigger_data: 触发数据
            branch: 目标分支

        Yields:
            SSE 事件: phase_update / log / complete / error
        """
        deployment_id = deployment_id or f"deploy-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
        logger.info(f"开始部署 [{deployment_id}], 触发方式: {trigger_type}, 分支: {branch}")

        initial_state: DeploymentState = {
            "deployment_id": deployment_id,
            "trigger_type": trigger_type,
            "trigger_data": trigger_data or {},
            "target_branch": branch,
            "commit_hash": "",
            "previous_commit_hash": "",
            "commit_message": "",
            "current_phase": "trigger",
            "phase_status": {},
            "phase_logs": [],
            "build_results": {},
            "verify_results": {},
            "needs_rollback": False,
            "rollback_status": "pending",
            "rollback_reason": "",
            "final_status": "running",
            "final_report": "",
            "error": "",
        }

        # 保存初始状态到 Redis
        await deployment_memory.save_state(deployment_id, dict(initial_state))

        config_dict = {"configurable": {"thread_id": deployment_id}}

        try:
            async for event in self.graph.astream(
                input=initial_state,
                config=config_dict,
                stream_mode="updates",
            ):
                for node_name, node_output in event.items():
                    if not node_output:
                        continue

                    # 更新 Redis 状态
                    full_state = self.graph.get_state(config_dict)
                    if full_state and full_state.values:
                        await deployment_memory.save_state(deployment_id, full_state.values)

                    # 发送阶段更新事件
                    phase = node_output.get("current_phase", node_name)
                    phase_status = node_output.get("phase_status", {})
                    current_status = phase_status.get(phase, "running") if phase_status else "running"

                    yield {
                        "type": "phase_update",
                        "phase": phase,
                        "status": current_status,
                        "phase_label": PHASE_NAMES.get(phase, phase),
                    }

                    # 发送日志事件
                    phase_logs = node_output.get("phase_logs", [])
                    if isinstance(phase_logs, list):
                        for log_entry in phase_logs:
                            if isinstance(log_entry, tuple) and len(log_entry) == 3:
                                log_phase, log_msg, log_ts = log_entry
                                yield {
                                    "type": "log",
                                    "phase": log_phase,
                                    "message": log_msg,
                                    "timestamp": log_ts,
                                }
                                await deployment_memory.append_log(deployment_id, log_phase, log_msg)

                    # 发送构建和验证结果
                    if "build_results" in node_output:
                        yield {
                            "type": "build_results",
                            "data": node_output["build_results"],
                        }
                    if "verify_results" in node_output:
                        yield {
                            "type": "verify_results",
                            "data": node_output["verify_results"],
                        }

                    # 检查是否需要回滚
                    if node_output.get("needs_rollback"):
                        reason = node_output.get("error", "未知错误")
                        yield {
                            "type": "rollback_started",
                            "reason": reason,
                        }

                    # 检查是否完成
                    if node_name == "complete":
                        final_status = node_output.get("final_status", "success")
                        final_report = node_output.get("final_report", "")
                        yield {
                            "type": "complete",
                            "final_status": final_status,
                            "deployment_id": deployment_id,
                            "report": final_report,
                        }

            logger.info(f"部署 [{deployment_id}] 完成")

        except Exception as e:
            error_msg = f"部署流程异常: {e}"
            logger.error(error_msg)
            yield {"type": "error", "message": error_msg, "deployment_id": deployment_id}

    async def cancel(self, deployment_id: str):
        """取消部署"""
        await deployment_memory.set_cancelled(deployment_id)
        logger.info(f"部署已取消: {deployment_id}")

    async def get_state(self, deployment_id: str) -> Dict[str, Any]:
        """获取部署状态"""
        state = await deployment_memory.get_state(deployment_id)

        # 补充日志
        logs = await deployment_memory.get_logs(deployment_id)
        state["logs"] = logs

        # 构建阶段列表
        phases = []
        phase_status = state.get("phase_status", {})
        if isinstance(phase_status, dict):
            for pname, pstatus in phase_status.items():
                phases.append({
                    "name": pname,
                    "label": PHASE_NAMES.get(pname, pname),
                    "status": pstatus,
                })
        state["phases"] = phases
        state["deployment_id"] = deployment_id

        return state

    async def get_history(self, page: int = 1, size: int = 20) -> Dict[str, Any]:
        """获取部署历史"""
        return await deployment_memory.list_history(page, size)


# 全局单例
deployment_service = DeploymentService()
