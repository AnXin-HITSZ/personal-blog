"""Agent 驱动 CI/CD 服务 — 编排 Plan-Execute-Replan 部署流水线"""

import os
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, Any, Optional

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from loguru import logger

from app.config import config
from app.agent.deploy_state import CICDState
from app.agent.deploy_nodes import cicd_planner, cicd_executor, cicd_replanner
from app.agent.deploy_tools.retrospective_tools import _default_template
from app.services.deployment_memory import deployment_memory

# 节点名称常量
NODE_INIT = "init_deploy"
NODE_PLANNER = "planner"
NODE_EXECUTOR = "executor"
NODE_REPLANNER = "replanner"
NODE_FINALIZE = "finalize_deploy"
NODE_RETROSPECTIVE = "retrospective"

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
    "retrospective": "经验总结",
}


async def init_deploy(state: CICDState) -> Dict[str, Any]:
    """前置节点：初始化部署环境，读取历史教训"""
    import subprocess
    from pathlib import Path

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

        # 读取 AGENTS.md 历史教训
        agents_path = Path(work_dir) / "AGENTS.md"
        lessons_loaded = ""
        if agents_path.exists():
            try:
                lessons_loaded = agents_path.read_text(encoding="utf-8")
                logger.info(f"已加载 AGENTS.md 历史教训（{len(lessons_loaded)} 字符）")
            except Exception as e:
                logger.warning(f"读取 AGENTS.md 失败: {e}")
                lessons_loaded = ""
        else:
            logger.info("AGENTS.md 尚不存在，无历史教训可加载")

        phase_status = {
            "init_deploy": "success",
            "planner": "pending",
            "executor": "pending",
            "replanner": "pending",
            "complete": "pending",
            "retrospective": "pending",
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
            "lessons_loaded": lessons_loaded,
            "start_time": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"初始化失败: {e}")
        return {
            "current_phase": "init_deploy",
            "phase_status": {"init_deploy": "failed"},
            "phase_logs": [("init_deploy", f"初始化失败: {e}", "")],
            "final_status": "failed",
            "error": str(e),
            "start_time": datetime.now(timezone.utc).isoformat(),
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


async def cicd_retrospective(state: CICDState) -> Dict[str, Any]:
    """回顾节点：总结部署经验教训，写入 AGENTS.md

    在 finalize_deploy 之后执行。只对 success/failed 状态做总结。
    调用 LLM 分析部署数据并生成结构化教训，追加到 AGENTS.md 并 git commit。
    """
    import subprocess
    from pathlib import Path

    logger.info("=== 部署回顾：总结教训 ===")

    final_status = state.get("final_status", "failed")
    deployment_id = state.get("deployment_id", "unknown")

    # 跳过 cancelled 状态的教训总结
    if final_status == "cancelled":
        logger.info("部署已取消，跳过教训总结")
        return {
            "current_phase": "retrospective",
            "phase_status": {"retrospective": "skipped"},
            "phase_logs": [("retrospective", "部署已取消，跳过教训总结", "")],
        }

    # 收集部署数据
    fix_attempts = state.get("fix_attempts", 0)
    error_log = state.get("error_log", "")
    phase_logs = state.get("phase_logs", [])
    past_steps = state.get("past_steps", [])
    commit_message = state.get("commit_message", "")
    start_time_str = state.get("start_time", "")

    # 计算部署耗时
    duration_str = "unknown"
    if start_time_str:
        try:
            start = datetime.fromisoformat(start_time_str)
            now = datetime.now(timezone.utc)
            delta = now - start
            minutes, seconds = divmod(int(delta.total_seconds()), 60)
            duration_str = f"{minutes}m{seconds}s"
        except Exception:
            pass

    # 格式化执行步骤摘要
    steps_summary = ""
    if past_steps:
        lines = []
        for step, result in past_steps:
            result_preview = (str(result) or "")[:200].replace("\n", " ")
            lines.append(f"  - {step}")
            if result_preview:
                lines.append(f"    结果: {result_preview}")
        steps_summary = "\n".join(lines)

    # 格式化日志摘要
    logs_summary = ""
    if phase_logs:
        log_lines = [f"  - {msg}" for _, msg, _ in phase_logs[-10:]]
        logs_summary = "\n".join(log_lines)

    # 调用 LLM 生成教训总结
    try:
        from langchain_core.prompts import ChatPromptTemplate
        from pydantic import BaseModel, Field

        class DeploymentLesson(BaseModel):
            problem: str = Field(description="出了什么问题（一句话概括）")
            root_cause: str = Field(description="根本原因分析")
            prevention: str = Field(description="下次如何预防（具体可操作的步骤）")
            impact: str = Field(description="造成的影响（如无则留空）")

        RETRO_PROMPT = """你是一个 CI/CD 部署回顾分析师。分析以下部署数据，生成一条经验教训。

部署数据：
- 部署 ID: {deployment_id}
- 最终状态: {final_status}
- 部署耗时: {duration}
- 提交信息: {commit_message}
- 修复尝试次数: {fix_attempts}
- 错误日志: {error_log}
- 执行步骤:
{steps_summary}
- 部署日志（最近）:
{logs_summary}

请分析本次部署，生成结构化的教训总结。注意：
- 如果是 success，重点总结"做对了什么"和"如何保持"
- 如果是 failed，重点总结"哪里出了问题"和"如何避免"
- 如果没什么可总结的（一切顺利且无特殊），生成一条简短的正面记录"""

        llm = ChatOpenAI(
            model=config.llm_model_id,
            api_key=config.llm_api_key,
            base_url=config.llm_base_url,
            temperature=0,
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", RETRO_PROMPT),
            ("placeholder", "{messages}"),
        ])

        chain = prompt | llm.with_structured_output(DeploymentLesson)
        lesson = await chain.ainvoke({
            "messages": [],
            "deployment_id": deployment_id,
            "final_status": final_status,
            "duration": duration_str,
            "commit_message": commit_message,
            "fix_attempts": str(fix_attempts),
            "error_log": error_log[:500] if error_log else "（无）",
            "steps_summary": steps_summary or "（无）",
            "logs_summary": logs_summary or "（无）",
        })

        if isinstance(lesson, DeploymentLesson):
            problem = lesson.problem
            root_cause = lesson.root_cause
            prevention = lesson.prevention
            impact = lesson.impact
        else:
            problem = lesson.get("problem", "部署完成")
            root_cause = lesson.get("root_cause", "常规部署")
            prevention = lesson.get("prevention", "无特殊注意事项")
            impact = lesson.get("impact", "")

    except Exception as e:
        logger.warning(f"LLM 教训总结失败，使用默认内容: {e}")
        problem = "部署完成"
        root_cause = "常规部署"
        prevention = "无特殊注意事项"
        impact = ""

    # 写入 AGENTS.md
    date_str = datetime.now().strftime("%Y-%m-%d")
    entry = (
        f"\n"
        f"### {date_str} | {deployment_id} | {final_status}\n"
        f"- **问题**: {problem}\n"
        f"- **根因**: {root_cause}\n"
        f"- **预防**: {prevention}\n"
    )
    if impact:
        entry += f"- **影响**: {impact}\n"

    agents_path = Path(config.deploy_work_dir) / "AGENTS.md"
    try:
        if agents_path.exists():
            content = agents_path.read_text(encoding="utf-8")
        else:
            content = _default_template()

        # 在第一个 "---" 分隔符之后追加
        separator = "---\n"
        sep_idx = content.find(separator)
        if sep_idx != -1:
            insert_pos = sep_idx + len(separator)
            new_content = content[:insert_pos] + entry + content[insert_pos:]
        else:
            new_content = content + "\n" + entry

        agents_path.write_text(new_content, encoding="utf-8")
        logger.info(f"AGENTS.md 已追加教训: {problem[:60]}")

        # git add + commit（不 push）
        try:
            subprocess.run(
                ["git", "add", "AGENTS.md"],
                capture_output=True, text=True,
                cwd=config.deploy_work_dir, timeout=30,
            )
            subprocess.run(
                ["git", "commit", "-m", f"docs: add deployment lesson from {deployment_id}", "--allow-empty"],
                capture_output=True, text=True,
                cwd=config.deploy_work_dir, timeout=30,
            )
            logger.info(f"AGENTS.md 已提交 git")
        except Exception as e:
            logger.warning(f"git commit AGENTS.md 失败: {e}")

        return {
            "current_phase": "retrospective",
            "phase_status": {"retrospective": "success"},
            "phase_logs": [
                ("retrospective", f"部署回顾完成，状态: {final_status}", ""),
                ("retrospective", f"教训: {problem[:80]}", ""),
                ("retrospective", f"预防: {prevention[:80]}", ""),
            ],
        }

    except Exception as e:
        logger.error(f"写入 AGENTS.md 失败: {e}")
        return {
            "current_phase": "retrospective",
            "phase_status": {"retrospective": "failed"},
            "phase_logs": [("retrospective", f"写入教训失败: {e}", "")],
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

        workflow.add_node(NODE_RETROSPECTIVE, cicd_retrospective)
        workflow.add_edge(NODE_FINALIZE, NODE_RETROSPECTIVE)
        workflow.add_edge(NODE_RETROSPECTIVE, END)

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
            "lessons_loaded": "",
            "start_time": "",
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
