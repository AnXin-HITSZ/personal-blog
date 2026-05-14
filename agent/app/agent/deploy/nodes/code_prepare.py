"""阶段二：代码准备节点"""

import subprocess
from datetime import datetime
from typing import Dict, Any

from loguru import logger

from app.config import config
from ..state import DeploymentState


async def code_prepare_node(state: DeploymentState) -> Dict[str, Any]:
    """阶段二：代码准备

    1. git fetch 获取最新代码
    2. 检查是否有新的提交
    3. git pull 拉取代码
    4. 检查冲突
    5. 记录新 commit hash
    """
    logger.info("=== 阶段二：代码准备 ===")

    deployment_id = state["deployment_id"]
    target_branch = state["target_branch"]
    work_dir = config.deploy_work_dir
    phase_logs = list(state.get("phase_logs", []))
    phase_status = dict(state.get("phase_status", {}))

    try:
        # 1. git fetch
        phase_logs.append(("code_prepare", "正在 fetch 远程代码...", datetime.now().isoformat()))
        logger.info("执行 git fetch...")

        fetch_result = subprocess.run(
            ["git", "fetch", "origin", target_branch],
            capture_output=True, text=True, cwd=work_dir, timeout=60
        )
        if fetch_result.returncode != 0:
            raise RuntimeError(f"git fetch 失败: {fetch_result.stderr.strip()}")

        phase_logs.append(("code_prepare", "fetch 完成", datetime.now().isoformat()))

        # 2. 检查是否有新提交
        result = subprocess.run(
            ["git", "rev-list", "--count", f"HEAD..origin/{target_branch}"],
            capture_output=True, text=True, cwd=work_dir, timeout=30
        )
        ahead_count = int(result.stdout.strip() or "0")

        if ahead_count == 0:
            logger.info("没有新的提交，跳过")
            phase_logs.append(("code_prepare", "没有新的提交，无需更新", datetime.now().isoformat()))
            phase_status["code_prepare"] = "skipped"

            return {
                "current_phase": "code_prepare",
                "phase_status": phase_status,
                "phase_logs": phase_logs,
            }

        phase_logs.append(("code_prepare", f"检测到 {ahead_count} 个新提交", datetime.now().isoformat()))

        # 3. git pull
        phase_logs.append(("code_prepare", "正在拉取代码...", datetime.now().isoformat()))
        pull_result = subprocess.run(
            ["git", "pull", "origin", target_branch],
            capture_output=True, text=True, cwd=work_dir, timeout=120
        )
        if pull_result.returncode != 0:
            raise RuntimeError(f"git pull 失败: {pull_result.stderr.strip()}")

        phase_logs.append(("code_prepare", "代码拉取完成", datetime.now().isoformat()))

        # 4. 检查冲突
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=work_dir, timeout=30
        )
        if "UU " in status_result.stdout or "AA " in status_result.stdout:
            error_msg = f"检测到合并冲突: {status_result.stdout.strip()}"
            logger.error(error_msg)
            phase_logs.append(("code_prepare", error_msg, datetime.now().isoformat()))
            phase_status["code_prepare"] = "failed"
            return {
                "current_phase": "code_prepare",
                "phase_status": phase_status,
                "phase_logs": phase_logs,
                "needs_rollback": True,
                "error": error_msg,
            }

        # 5. 记录新的 commit hash
        hash_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd=work_dir, timeout=30
        )
        new_hash = hash_result.stdout.strip()

        msg_result = subprocess.run(
            ["git", "log", "-1", "--pretty=format:%s"],
            capture_output=True, text=True, cwd=work_dir, timeout=30
        )
        commit_message = msg_result.stdout.strip()

        phase_logs.append(("code_prepare", f"更新到 {new_hash}: {commit_message}", datetime.now().isoformat()))
        phase_status["code_prepare"] = "success"

        logger.info(f"代码准备完成: {new_hash}")

        return {
            "current_phase": "code_prepare",
            "commit_hash": new_hash,
            "commit_message": commit_message,
            "phase_status": phase_status,
            "phase_logs": phase_logs,
        }

    except Exception as e:
        error_msg = f"代码准备失败: {e}"
        logger.error(error_msg)
        phase_logs.append(("code_prepare", error_msg, datetime.now().isoformat()))
        phase_status["code_prepare"] = "failed"
        return {
            "current_phase": "code_prepare",
            "phase_status": phase_status,
            "phase_logs": phase_logs,
            "needs_rollback": True,
            "error": error_msg,
        }
