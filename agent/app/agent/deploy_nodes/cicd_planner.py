"""
CI/CD Planner 节点：制定部署计划

复用 AIOps planner.py 的架构：
- ChatOpenAI + with_structured_output(Plan)
- ChatPromptTemplate 驱动
- 失败时降级到默认计划
"""

from typing import Dict, Any, List

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from loguru import logger

from app.config import config
from app.agent.deploy_prompts import CICD_PLANNER_PROMPT
from app.agent.deploy_tools import (
    git_pull, npm_build, maven_build, docker_build,
    docker_deploy, health_check, get_git_diff,
    read_log, read_file, edit_file, run_command,
)
from app.agent.aiops.utils import format_tools_description
from ..deploy_state import CICDState


class CICDPlan(BaseModel):
    """CI/CD 计划的输出格式"""
    steps: List[str] = Field(
        description="部署任务所需的执行步骤。这些步骤应该按顺序执行，每一步都建立在前一步的基础上。"
    )


# Planner 提示词
planner_prompt = ChatPromptTemplate.from_messages([
    ("system", CICD_PLANNER_PROMPT),
    ("placeholder", "{messages}"),
])


async def cicd_planner(state: CICDState) -> Dict[str, Any]:
    """
    CI/CD 规划节点

    1. 收集可用工具列表
    2. 调用 LLM 生成结构化部署计划
    3. 失败时降级到默认计划
    """
    logger.info("=== CI/CD Planner：制定部署计划 ===")

    input_text = state.get("input", "")
    target_branch = state.get("target_branch", "main")
    max_retries = state.get("max_retries", 2)
    logger.info(f"部署请求: {input_text}, 分支: {target_branch}")

    try:
        # 获取可用工具列表
        all_tools = [
            git_pull, npm_build, maven_build, docker_build,
            docker_deploy, health_check, get_git_diff,
            read_log, read_file, edit_file, run_command,
        ]
        tools_description = format_tools_description(all_tools)

        # 调用 LLM 生成计划
        llm = ChatOpenAI(
            model=config.llm_model_id,
            api_key=config.llm_api_key,
            base_url=config.llm_base_url,
            temperature=0,
        )

        planner_chain = planner_prompt | llm.with_structured_output(CICDPlan)
        plan_result = await planner_chain.ainvoke({
            "messages": [("user", input_text)],
            "tools_description": tools_description,
            "branch": target_branch,
            "max_retries": str(max_retries),
        })

        # 提取步骤列表
        if isinstance(plan_result, CICDPlan):
            plan_steps = plan_result.steps
        else:
            plan_steps = plan_result.get("steps", [])

        logger.info(f"计划已生成，共 {len(plan_steps)} 个步骤")
        for i, step in enumerate(plan_steps, 1):
            logger.info(f"  步骤{i}: {step}")

        return {
            "plan": plan_steps,
            "current_phase": "planner",
            "phase_status": {"planner": "success"},
            "phase_logs": [("planner", f"AI 规划完成，共 {len(plan_steps)} 个步骤", "")],
        }

    except Exception as e:
        logger.error(f"LLM 规划失败，降级到默认计划: {e}")
        # 降级到默认计划
        default_steps = [
            f"git_pull: 拉取 {target_branch} 分支最新代码",
            "npm_build: 构建前端项目",
            "maven_build: 构建后端项目",
            "docker_build: 构建 Docker 镜像",
            "docker_deploy: 部署并启动服务",
            "health_check: 验证服务健康状态",
        ]
        logger.info("使用默认计划（6 个标准步骤）")
        return {
            "plan": default_steps,
            "current_phase": "planner",
            "phase_status": {"planner": "success"},
            "phase_logs": [("planner", "LLM 规划失败，降级到默认计划", "")],
        }
