"""Agent 驱动 CI/CD 服务 — 编排 Plan-Execute-Replan 部署流水线"""

import uuid
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, Optional

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from loguru import logger

from app.config import config
from app.agent.deploy_state import CICDState
from app.agent.deploy_nodes import cicd_planner, cicd_executor, cicd_replanner
from app.services.deployment_memory import deployment_memory

# 节点名称常量
NODE_INIT = "init_deploy"
NODE_PLANNER = "planner"
NODE_EXECUTOR = "executor"
NODE_REPLANNER = "replanner"
NODE_FINALIZE = "finalize_deploy"

# 阶段名称映射（前端兼容）
PHASE_NAMES = {
    "init_deploy": "初始化部署",
    "planner": "AI 规划部署",
    "executor": "执行部署步骤",
    "replanner": "AI 评估状态",
    "repair": "AI 自修复",
    "code_prepare": "代码准备",
    "build_test": "构建测试",
    "deploy": "部署发布",
    "verify": "验证服务",
    "complete": "完成收尾",
    "finalize_deploy": "完成收尾",
}


async def init_deploy(state: CICDState) -> Dict[str, Any]:
    """前置节点：初始化部署环境"""
    import subprocess

    logger.info("=== 初始化部署 ===")
    work_dir = config.deploy_work_dir
    deployment_id = state.get("deployment_id", "")

    try:
        # 获取当前 HEAD
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd=work_dir, timeout=30,
        )
        current_hash = result.stdout.strip()

        # 获取 commit message
        msg_result = subprocess.run(
            ["git", "log", "-1", "--pretty=format:%s"],
            capture_output=True, text=True, cwd=work_dir, timeout=30,
        )
        commit_msg = msg_result.stdout.strip()

        phase_status = {
            "init_deploy": "success",
            "planner": "pending",
            "executor": "pending",
            "replanner": "pending",
            "complete": "pending",
        }

        logger.info(f"初始化完成: {current_hash}")
        return {
            "deployment_id": deployment_id,
            "commit_hash": current_hash,
            "previous_commit_hash": current_hash,
            "commit_message": commit_msg,
            "current_phase": "init_deploy",
            "phase_status": phase_status,
            "phase_logs": [
                ("init_deploy", f"触发方式: {state.get('trigger_type', 'manual')}", ""),
                ("init_deploy", f"目标分支: {state.get('target_branch', 'main')}", ""),
                ("init_deploy", f"当前 HEAD: {current_hash}", ""),
                ("init_deploy", f"提交信息: {commit_msg}", ""),
            ],
            "final_status": "running",
            "fix_attempts": 0,
            "error_log": "",
            "needs_approval": False,
            "approval_granted": False,
            "pending_diff": "",
        }

    except Exception as e:
        logger.error(f"初始化失败: {e}")
        return {
            "current_phase": "init_deploy",
            "phase_status": {"init_deploy": "failed"},
            "phase_logs": [("init_deploy", f"初始化失败: {e}", "")],
            "final_status": "failed",
            "error": str(e),
        }


async def finalize_deploy(state: CICDState) -> Dict[str, Any]:
    """后置节点：收尾并生成 git tag"""
    import subprocess

    logger.info("=== 完成收尾 ===")

    final_status = state.get("final_status", "failed")
    deployment_id = state.get("deployment_id", "")

    # 成功时创建 git tag
    if final_status == "success":
        try:
            commit_msg = state.get("commit_message", "deploy")
            tag_name = f"deploy-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            subprocess.run(
                ["git", "tag", "-a", tag_name, "-m", f"Auto deploy: {commit_msg}"],
                capture_output=True, text=True,
                cwd=config.deploy_work_dir, timeout=30,
            )
            logger.info(f"Git tag 已创建: {tag_name}")
        except Exception as e:
            logger.warning(f"创建 git tag 失败: {e}")

    return {
        "current_phase": "finalize_deploy",
        "phase_status": {"complete": final_status},
        "phase_logs": [("complete", f"部署完成，状态: {final_status}", "")],
    }


def should_continue(state: CICDState) -> str:
    """Replanner 条件边：决定继续执行还是结束"""
    if state.get("response") or state.get("final_status") in ("success", "failed", "cancelled"):
        logger.info(f"流程结束，final_status={state.get('final_status')}")
        return NODE_FINALIZE
    plan = state.get("plan", [])
    if plan:
        logger.info(f"继续执行，剩余 {len(plan)} 个步骤")
        return NODE_EXECUTOR
    logger.info("计划为空，生成最终响应")
    return NODE_FINALIZE


class CICDService:
    """Agent 驱动 CI/CD 服务"""

    def __init__(self):
        self.checkpointer = MemorySaver()
        self.graph = self._build_graph()
        logger.info("CICDService 初始化完成")

    def _build_graph(self):
        """构建 CI/CD Agent 工作流"""
        workflow = StateGraph(CICDState)

        # 确定性节点
        workflow.add_node(NODE_INIT, init_deploy)
        workflow.add_node(NODE_FINALIZE, finalize_deploy)

        # PER 循环节点
        workflow.add_node(NODE_PLANNER, cicd_planner)
        workflow.add_node(NODE_EXECUTOR, cicd_executor)
        workflow.add_node(NODE_REPLANNER, cicd_replanner)

        # 流程
        workflow.set_entry_point(NODE_INIT)
        workflow.add_edge(NODE_INIT, NODE_PLANNER)
        workflow.add_edge(NODE_PLANNER, NODE_EXECUTOR)
        workflow.add_edge(NODE_EXECUTOR, NODE_REPLANNER)

        # 条件边
        workflow.add_conditional_edges(
            NODE_REPLANNER,
            should_continue,
            {
                NODE_EXECUTOR: NODE_EXECUTOR,
                NODE_FINALIZE: NODE_FINALIZE,
            }
        )

        workflow.add_edge(NODE_FINALIZE, END)

        return workflow.compile(checkpointer=self.checkpointer)

    async def execute(
        self,
        trigger_type: str = "manual",
        branch: str = "main",
        deployment_id: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """执行 Agent 驱动部署

        Yields:
            SSE 兼容事件（phase_update / log / agent_thought / fix_attempt / complete / error）
        """
        deployment_id = deployment_id or (
            f"deploy-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
        )
        logger.info(f"开始 Agent 部署 [{deployment_id}], 分支: {branch}")

        initial_state: CICDState = {
            "input": f"部署 {branch} 分支最新代码到生产环境",
            "plan": [],
            "past_steps": [],
            "response": "",
            "deployment_id": deployment_id,
            "trigger_type": trigger_type,
            "target_branch": branch,
            "commit_hash": "",
            "previous_commit_hash": "",
            "commit_message": "",
            "final_status": "running",
            "current_phase": "",
            "phase_status": {},
            "phase_logs": [],
            "build_results": {},
            "verify_results": {},
            "fix_attempts": 0,
            "max_retries": 2,
            "error_log": "",
            "needs_approval": False,
            "approval_granted": False,
            "pending_diff": "",
        }

        # 保存初始状态到 Redis
        await deployment_memory.save_state(deployment_id, dict(initial_state))  # type: ignore

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

                    # 持久化到 Redis
                    full_state = self.graph.get_state(config_dict)
                    if full_state and full_state.values:
                        await deployment_memory.save_state(deployment_id, full_state.values)

                    # 生成前端兼容事件
                    async for sse_event in self._format_event(node_name, node_output, deployment_id):
                        yield sse_event

            logger.info(f"部署 [{deployment_id}] 完成")

        except Exception as e:
            error_msg = f"Agent 部署流程异常: {e}"
            logger.error(error_msg)
            yield {"type": "error", "message": error_msg, "deployment_id": deployment_id}

    async def _format_event(self, node_name: str, output: Dict, deploy_id: str):
        """将节点输出格式化为前端兼容的 SSE 事件"""
        phase = output.get("current_phase", node_name)
        phase_status = output.get("phase_status", {})
        current_status = phase_status.get(phase, "running") if phase_status else "running"

        # ── 阶段更新事件 ──
        yield {
            "type": "phase_update",
            "phase": phase,
            "status": current_status,
            "phase_label": PHASE_NAMES.get(phase, phase),
        }

        # ── 日志事件 ──
        phase_logs = output.get("phase_logs", [])
        if isinstance(phase_logs, list):
            for log_entry in phase_logs:
                if isinstance(log_entry, tuple) and len(log_entry) >= 2:
                    log_phase = log_entry[0]
                    log_msg = log_entry[1]
                    yield {
                        "type": "log",
                        "phase": log_phase,
                        "message": log_msg,
                        "timestamp": log_entry[2] if len(log_entry) > 2 else "",
                    }
                    await deployment_memory.append_log(deploy_id, log_phase, log_msg)

        # ── Agent 思考事件（新增） ──
        if node_name == NODE_PLANNER:
            plan = output.get("plan", [])
            yield {
                "type": "agent_thought",
                "content": f"AI 已制定部署计划，共 {len(plan)} 个步骤",
                "phase": "planner",
                "plan": plan,
            }

        # ── 修复尝试事件（新增） ──
        if node_name == NODE_REPLANNER:
            fix_attempts = output.get("fix_attempts", 0)
            if "repair" in phase or fix_attempts > 0:
                yield {
                    "type": "fix_attempt",
                    "attempt": fix_attempts,
                    "max_retries": 2,
                    "phase": "repair",
                }

        # ── past_steps 中包含 LLM 工具调用信息 ──
        past_steps = output.get("past_steps", [])
        if isinstance(past_steps, list) and past_steps:
            last_task, last_result = past_steps[-1]
            # 检查结果长度，长文本可能是工具输出
            if len(str(last_result)) > 50:
                yield {
                    "type": "agent_thought",
                    "content": f"步骤完成: {last_task[:100]}",
                    "phase": phase,
                    "detail": str(last_result)[:500],
                }

        # ── 构建/验证结果 ──
        if "build_results" in output:
            yield {"type": "build_results", "data": output["build_results"]}
        if "verify_results" in output:
            yield {"type": "verify_results", "data": output["verify_results"]}

        # ── 完成事件 ──
        if node_name == NODE_FINALIZE or output.get("final_status") in ("success", "failed"):
            final_status = output.get("final_status", "success")
            final_report = output.get("response", "")
            yield {
                "type": "complete",
                "final_status": final_status,
                "deployment_id": deploy_id,
                "report": final_report,
            }

    async def cancel(self, deployment_id: str):
        """取消部署"""
        await deployment_memory.set_cancelled(deployment_id)
        logger.info(f"部署已取消: {deployment_id}")

    async def get_state(self, deployment_id: str) -> Dict[str, Any]:
        """获取部署状态（兼容原有接口）"""
        state = await deployment_memory.get_state(deployment_id)
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
cicd_service = CICDService()
