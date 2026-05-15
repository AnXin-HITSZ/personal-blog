"""
CI/CD Replanner 节点：决策下一步

复用 AIOps replanner.py 的架构：
- Act(BaseModel) 结构化输出（continue/replan/respond）
- 失败时降级到 continue 或 respond
- 硬限制步骤上限和重试上限
"""

from typing import Dict, Any, List

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from loguru import logger

from app.config import config
from app.agent.deploy_prompts import CICD_REPLANNER_PROMPT, CICD_REPORT_PROMPT
from app.agent.deploy_tools import (
    git_pull, npm_build, maven_build, docker_build,
    docker_deploy, health_check, get_git_diff,
    read_log, read_file, edit_file, run_command,
)
from app.agent.aiops.utils import format_tools_description
from ..deploy_state import CICDState


class CICDAct(BaseModel):
    """重新规划的输出格式"""
    action: str = Field(
        description="下一步的行动，必须是以下三种之一：\n"
        "- 'continue': 上一步成功，继续执行下一个步骤\n"
        "- 'replan': 上一步失败但可以修复，提供新的修复步骤\n"
        "- 'respond': 全部完成或不可恢复的错误，生成最终响应"
    )
    new_steps: List[str] = Field(
        default_factory=list,
        description="新的修复步骤列表（如果 action 是 'replan'）",
    )


class CICDReport(BaseModel):
    """最终部署报告的格式"""
    report: str = Field(description="结构化的部署总结报告，使用 Markdown 格式")


# Replanner 提示词
replanner_prompt = ChatPromptTemplate.from_messages([
    ("system", CICD_REPLANNER_PROMPT),
    ("placeholder", "{messages}"),
])

# 最终报告提示词
report_prompt = ChatPromptTemplate.from_messages([
    ("system", CICD_REPORT_PROMPT),
    ("placeholder", "{messages}"),
])


async def cicd_replanner(state: CICDState) -> Dict[str, Any]:
    """
    CI/CD 重新规划节点

    三种决策：
    1. continue — 上一步成功，继续执行
    2. replan — 步骤失败但可修复，生成修复步骤
    3. respond — 全部完成或不可恢复，生成报告
    """
    logger.info("=== CI/CD Replanner：重新规划 ===")

    plan = state.get("plan", [])
    past_steps = state.get("past_steps", [])
    fix_attempts = state.get("fix_attempts", 0)
    max_retries = state.get("max_retries", 2)
    target_branch = state.get("target_branch", "main")

    logger.info(f"剩余计划步骤: {len(plan)}")
    logger.info(f"已执行步骤: {len(past_steps)}")
    logger.info(f"当前修复尝试: {fix_attempts}/{max_retries}")

    # ═══ 硬限制检查 ═══

    # 1. 步骤上限
    MAX_STEPS = 15
    if len(past_steps) >= MAX_STEPS:
        logger.warning(f"已执行 {len(past_steps)} 步，超过上限 {MAX_STEPS}，强制生成报告")
        return await _generate_report(state)

    # 2. 检查上一步是否失败（past_steps 的最后一条）
    last_step_successful = True
    if past_steps:
        last_task, last_result = past_steps[-1]
        if "失败" in str(last_result) or "❌" in str(last_result) or "⚠️" in str(last_result):
            last_step_successful = False
            logger.warning(f"上一步失败: {last_task[:50]}")

    # 如果没有剩余计划且上一步成功 → 完成
    if not plan and last_step_successful:
        logger.info("所有步骤已完成，生成部署报告")
        return await _generate_report(state)

    # 如果上一步成功且有剩余计划 → continue
    if last_step_successful and plan:
        logger.info("上一步成功，继续执行")
        return {"current_phase": "replanner"}

    # ═══ 上一步失败 — 判断是否可修复 ═══
    if not last_step_successful:
        if fix_attempts >= max_retries:
            logger.warning(f"已重试 {fix_attempts} 次，达到上限，终止部署")
            return await _generate_report(state)

        # 尝试 LLM 决策是否 replan
        return await _decide_replan(state)

    # 默认：继续
    return {}


async def _decide_replan(state: CICDState) -> Dict[str, Any]:
    """尝试让 LLM 决定是否 replan，失败时降级到 respond"""
    plan = state.get("plan", [])
    past_steps = state.get("past_steps", [])
    target_branch = state.get("target_branch", "main")

    try:
        all_tools = [
            git_pull, npm_build, maven_build, docker_build,
            docker_deploy, health_check, get_git_diff,
            read_log, read_file, edit_file, run_command,
        ]
        tools_description = format_tools_description(all_tools)

        # 格式化已执行的步骤
        steps_summary = "\n".join([
            f"步骤: {step}\n结果: {str(result)[:300]}..."
            for step, result in past_steps
        ])

        llm = ChatOpenAI(
            model=config.llm_model_id,
            api_key=config.llm_api_key,
            base_url=config.llm_base_url,
            temperature=0,
        )

        replanner_chain = replanner_prompt | llm.with_structured_output(CICDAct)
        act = await replanner_chain.ainvoke({
            "messages": [
                ("user", f"原始任务: 部署 {target_branch} 分支"),
                ("user", f"已执行的步骤:\n{steps_summary}"),
                ("user", f"剩余计划: {', '.join(plan) if plan else '无'}"),
            ],
            "tools_description": tools_description,
            "execution_history": steps_summary,
            "remaining_plan": ", ".join(plan) if plan else "无",
            "max_retries": str(state.get("max_retries", 2)),
        })

        if isinstance(act, CICDAct):
            action = act.action
            new_steps = act.new_steps
        else:
            action = act.get("action", "respond")
            new_steps = act.get("new_steps", [])

        logger.info(f"Replanner 决策: {action}")

        if action == "replan" and new_steps:
            # 限制新步骤数不能超过剩余计划数（或默认 3）
            max_new = max(len(plan), 3) if plan else 3
            if len(new_steps) > max_new:
                new_steps = new_steps[:max_new]

            logger.info(f"决定修复，生成 {len(new_steps)} 个修复步骤")
            return {
                "plan": new_steps,
                "fix_attempts": state.get("fix_attempts", 0) + 1,
                "current_phase": "repair",
            }

        elif action == "continue":
            logger.info("决定继续执行")
            return {}

        else:
            logger.info("决定生成最终报告")
            return await _generate_report(state)

    except Exception as e:
        logger.error(f"Replanner 决策失败: {e}")
        # 降级：记录错误，尝试继续或结束
        if state.get("plan"):
            logger.info("降级：继续执行剩余计划")
            return {}
        else:
            return await _generate_report(state)


async def _generate_report(state: CICDState) -> Dict[str, Any]:
    """用 LLM 或降级逻辑生成最终部署报告"""
    past_steps = state.get("past_steps", [])
    plan = state.get("plan", [])

    # 确定最终状态
    has_failure = any(
        "失败" in str(r) or "❌" in str(r) or "⚠️" in str(r)
        for _, r in past_steps
    )

    try:
        llm = ChatOpenAI(
            model=config.llm_model_id,
            api_key=config.llm_api_key,
            base_url=config.llm_base_url,
            temperature=0,
        )

        # 格式化执行历史
        execution_history = "\n\n".join([
            f"### 步骤: {step}\n**结果:**\n{result}"
            for step, result in past_steps
        ])

        report_chain = report_prompt | llm.with_structured_output(CICDReport)
        report_obj = await report_chain.ainvoke({
            "messages": [
                ("user", f"部署任务: {state.get('input', '')}"),
                ("user", f"执行历史:\n{execution_history}"),
                ("user", "请基于以上信息生成部署报告"),
            ]
        })

        if isinstance(report_obj, CICDReport):
            final_report = report_obj.report
        else:
            final_report = report_obj.get("report", "")

    except Exception as e:
        logger.error(f"LLM 生成报告失败，使用模板: {e}")
        # 降级生成报告
        final_report = _generate_fallback_report(state, has_failure)

    # 确定 final_status
    if has_failure:
        final_status = "failed"
    else:
        final_status = "success"

    logger.info(f"部署完成，最终状态: {final_status}")

    return {
        "response": final_report,
        "final_status": final_status,
        "current_phase": "complete",
        "phase_status": {"complete": final_status},
        "phase_logs": [("complete", f"部署完成: {final_status}", "")],
    }


def _generate_fallback_report(state: CICDState, has_failure: bool) -> str:
    """降级：用模板生成部署报告"""
    past_steps = state.get("past_steps", [])
    lines = []
    lines.append("# 部署报告\n")
    lines.append(f"- **部署 ID**: {state.get('deployment_id', 'N/A')}")
    lines.append(f"- **触发方式**: {state.get('trigger_type', 'manual')}")
    lines.append(f"- **目标分支**: {state.get('target_branch', 'main')}")
    lines.append(f"- **最终状态**: {'失败' if has_failure else '成功'}\n")

    if past_steps:
        lines.append("## 执行步骤\n")
        for i, (task, result) in enumerate(past_steps, 1):
            status = "✅" if not ("失败" in str(result) or "❌" in str(result)) else "❌"
            lines.append(f"### {status} 步骤 {i}: {task}")
            lines.append(f"```\n{str(result)[:300]}\n```\n")

    if has_failure:
        lines.append("## 错误信息")
        lines.append("\n部署过程中出现错误，请检查上述步骤详情。")

    return "\n".join(lines)
