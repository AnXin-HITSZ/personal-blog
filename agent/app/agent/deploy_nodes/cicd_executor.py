"""
CI/CD Executor 节点：执行部署步骤

复用 AIOps executor.py 的架构：
- LLM + bind_tools + ToolNode
- 自动执行工具调用并返回结果
"""

from typing import Dict, Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
from loguru import logger

from app.config import config
from app.agent.deploy_tools import (
    git_pull, npm_build, maven_build, docker_build,
    docker_deploy, health_check, get_git_diff,
    read_log, read_file, edit_file, run_command,
)
from ..deploy_state import CICDState


EXECUTOR_SYSTEM_PROMPT = """你是一个 CI/CD 执行专家，负责执行具体的部署步骤。

你可以使用各种工具来完成任务。对于每个步骤：
1. 理解步骤的目标
2. 选择合适的工具
3. 调用工具获取结果
4. 返回执行结果

注意：
- 如果工具调用失败，请说明失败原因
- 不要编造数据，只返回实际获取的信息
- 执行结果要清晰、准确
- 专注于当前步骤，不要考虑其他任务
"""


async def cicd_executor(state: CICDState) -> Dict[str, Any]:
    """
    CI/CD 执行节点：执行计划中的下一个步骤

    使用 LangGraph 的 ToolNode 自动处理工具调用
    """
    logger.info("=== CI/CD Executor：执行步骤 ===")

    plan = state.get("plan", [])

    if not plan:
        logger.info("计划为空，跳过执行")
        return {}

    # 取出第一个步骤
    task = plan[0]
    logger.info(f"当前任务: {task}")

    try:
        # 获取所有 CI/CD 工具
        all_tools = [
            git_pull, npm_build, maven_build, docker_build,
            docker_deploy, health_check, get_git_diff,
            read_log, read_file, edit_file, run_command,
        ]

        # 创建 LLM（绑定工具）
        llm = ChatOpenAI(
            model=config.llm_model_id,
            api_key=config.llm_api_key,
            base_url=config.llm_base_url,
            temperature=0,
        )
        llm_with_tools = llm.bind_tools(all_tools)

        # 创建工具节点
        tool_node = ToolNode(all_tools)

        # 构建消息
        messages = [
            SystemMessage(content=EXECUTOR_SYSTEM_PROMPT),
            HumanMessage(content=f"请执行以下部署任务: {task}"),
        ]

        # 第一步：LLM 决定是否调用工具
        llm_response = await llm_with_tools.ainvoke(messages)
        logger.info(f"LLM 响应类型: {type(llm_response).__name__}")

        # 第二步：如果有工具调用，执行工具
        if hasattr(llm_response, "tool_calls") and llm_response.tool_calls:
            logger.info(f"检测到 {len(llm_response.tool_calls)} 个工具调用")

            # 使用 ToolNode 自动执行工具
            messages.append(llm_response)
            tool_messages = await tool_node.ainvoke({"messages": messages})

            # 第三步：将工具结果返回给 LLM 生成最终答案
            messages.extend(tool_messages["messages"])
            final_response = await llm_with_tools.ainvoke(messages)
            result = final_response.content if hasattr(final_response, 'content') else str(final_response)
        else:
            # 没有工具调用，直接使用 LLM 的输出
            logger.info("LLM 未调用工具，直接返回结果")
            result = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)

        logger.info(f"步骤执行完成，结果长度: {len(str(result))}")

        # 检查步骤名称以确定阶段标记
        task_lower = task.lower()
        if "git_pull" in task_lower or "pull" in task_lower or "fetch" in task_lower:
            phase_name = "code_prepare"
        elif "npm" in task_lower or "前端" in task_lower:
            phase_name = "build_test"
        elif "maven" in task_lower or "后端" in task_lower:
            phase_name = "build_test"
        elif "docker" in task_lower and ("build" in task_lower or "镜像" in task_lower):
            phase_name = "build_test"
        elif "deploy" in task_lower or "部署" in task_lower or "up" in task_lower:
            phase_name = "deploy"
        elif "health" in task_lower or "验证" in task_lower or "check" in task_lower:
            phase_name = "verify"
        else:
            phase_name = "executor"

        return {
            "plan": plan[1:],  # 移除第一个步骤
            "past_steps": [(task, result)],  # 使用 operator.add 追加
            "current_phase": phase_name,
        }

    except Exception as e:
        logger.error(f"执行步骤失败: {e}", exc_info=True)
        return {
            "plan": plan[1:],
            "past_steps": [(task, f"执行失败: {str(e)}")],
        }
