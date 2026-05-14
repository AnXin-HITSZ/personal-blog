"""阶段一：触发更新节点"""

import subprocess
from datetime import datetime
from typing import Dict, Any

from loguru import logger

from app.config import config
from ..state import DeploymentState


# 预定义的阶段列表
PHASES = [
    "trigger",
    "code_prepare",
    "build_test",
    "deploy",
    "verify",
    "complete",
]


def _init_phase_status() -> Dict[str, str]:
    """初始化所有阶段状态为 pending"""
    return {p: "pending" for p in PHASES}


async def trigger_node(state: DeploymentState) -> Dict[str, Any]:
    """阶段一：触发更新

    验证触发来源，初始化部署状态：
    - 记录当前 commit hash（用于回滚）
    - 初始化 phase_status
    - 生成 deployment_id
    """
    logger.info("=== 阶段一：触发更新 ===")

    deployment_id = state.get("deployment_id", "")
    trigger_type = state.get("trigger_type", "manual")
    target_branch = state.get("target_branch", config.deploy_default_branch)

    try:
        # 切换到工作目录
        work_dir = config.deploy_work_dir

        # 获取当前 HEAD 哈希（用于回滚）
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd=work_dir, timeout=30
        )
        previous_hash = result.stdout.strip()

        # 获取当前 HEAD 的提交信息
        msg_result = subprocess.run(
            ["git", "log", "-1", "--pretty=format:%s"],
            capture_output=True, text=True, cwd=work_dir, timeout=30
        )
        commit_message = msg_result.stdout.strip()

        # 检查远程是否有更新
        logger.info(f"部署前 HEAD: {previous_hash}")
        logger.info(f"提交信息: {commit_message}")

        # 初始化阶段状态
        phase_status = _init_phase_status()
        phase_status["trigger"] = "success"

        return {
            "deployment_id": deployment_id,
            "trigger_type": trigger_type,
            "target_branch": target_branch,
            "commit_hash": previous_hash,
            "previous_commit_hash": previous_hash,
            "commit_message": commit_message,
            "current_phase": "trigger",
            "phase_status": phase_status,
            "phase_logs": [
                ("trigger", f"触发方式: {trigger_type}", datetime.now().isoformat()),
                ("trigger", f"目标分支: {target_branch}", datetime.now().isoformat()),
                ("trigger", f"当前 HEAD: {previous_hash}", datetime.now().isoformat()),
            ],
            "build_results": {},
            "verify_results": {},
            "needs_rollback": False,
            "rollback_status": "pending",
            "rollback_reason": "",
            "final_status": "running",
            "final_report": "",
            "error": "",
        }

    except subprocess.TimeoutExpired:
        msg = "获取 git 信息超时"
        logger.error(msg)
        return _error_state(state, deployment_id, msg)
    except Exception as e:
        msg = f"触发阶段失败: {e}"
        logger.error(msg)
        return _error_state(state, deployment_id, msg)


def _error_state(state: DeploymentState, deployment_id: str, error: str) -> Dict[str, Any]:
    """生成错误状态"""
    phase_status = state.get("phase_status", _init_phase_status())
    phase_status["trigger"] = "failed"
    return {
        "deployment_id": deployment_id,
        "current_phase": "trigger",
        "phase_status": phase_status,
        "phase_logs": [("trigger", error, datetime.now().isoformat())],
        "needs_rollback": True,
        "final_status": "failed",
        "error": error,
    }
