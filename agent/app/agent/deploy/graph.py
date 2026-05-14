"""部署流水线 LangGraph 图构建"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from loguru import logger

from .state import DeploymentState
from .nodes import (
    trigger_node,
    code_prepare_node,
    build_test_node,
    deploy_node,
    verify_node,
    complete_node,
    rollback_node,
)

# 节点名称常量
N_TRIGGER = "trigger"
N_CODE_PREPARE = "code_prepare"
N_BUILD_TEST = "build_test"
N_DEPLOY = "deploy"
N_VERIFY = "verify"
N_COMPLETE = "complete"
N_ROLLBACK = "rollback"


def build_deployment_graph():
    """构建部署流水线工作流图

    图结构：
        trigger → code_prepare → build_test → deploy → verify → complete → END
                                                                  ↓
                                                            (failed时) rollback → complete → END
    """
    logger.info("构建部署流水线图...")

    workflow = StateGraph(DeploymentState)

    # 添加节点
    workflow.add_node(N_TRIGGER, trigger_node)
    workflow.add_node(N_CODE_PREPARE, code_prepare_node)
    workflow.add_node(N_BUILD_TEST, build_test_node)
    workflow.add_node(N_DEPLOY, deploy_node)
    workflow.add_node(N_VERIFY, verify_node)
    workflow.add_node(N_COMPLETE, complete_node)
    workflow.add_node(N_ROLLBACK, rollback_node)

    # 设置入口
    workflow.set_entry_point(N_TRIGGER)

    # 主流程边
    workflow.add_edge(N_TRIGGER, N_CODE_PREPARE)
    workflow.add_edge(N_CODE_PREPARE, N_BUILD_TEST)
    workflow.add_edge(N_BUILD_TEST, N_DEPLOY)
    workflow.add_edge(N_DEPLOY, N_VERIFY)

    # Verify 的条件边
    def after_verify(state: DeploymentState) -> str:
        """验证后判断：失败则回滚，成功则完成"""
        if state.get("needs_rollback", False):
            logger.warning("验证失败，进入回滚流程")
            return N_ROLLBACK
        return N_COMPLETE

    workflow.add_conditional_edges(
        N_VERIFY,
        after_verify,
        {N_ROLLBACK: N_ROLLBACK, N_COMPLETE: N_COMPLETE},
    )

    # 回滚后也进入完成节点
    workflow.add_edge(N_ROLLBACK, N_COMPLETE)

    # 完成后结束
    workflow.add_edge(N_COMPLETE, END)

    # 编译
    checkpointer = MemorySaver()
    compiled = workflow.compile(checkpointer=checkpointer)
    logger.info("部署流水线图构建完成")
    return compiled
