"""回滚节点"""

import subprocess
import time
from datetime import datetime
from typing import Dict, Any

from loguru import logger

from app.config import config
from ..state import DeploymentState


async def rollback_node(state: DeploymentState) -> Dict[str, Any]:
    """回滚到上一版本

    1. git checkout 到 previous_commit_hash
    2. 重新构建（npm + maven + docker）
    3. 重新部署（docker compose up）
    4. 重新验证
    """
    logger.info("=== 回滚节点 ===")

    phase_logs = list(state.get("phase_logs", []))
    phase_status = dict(state.get("phase_status", {}))
    old_hash = state.get("previous_commit_hash", "")
    work_dir = config.deploy_work_dir
    deploy_dir = f"{work_dir}/deploy"

    phase_logs.append(("rollback", f"开始回滚到 {old_hash}", datetime.now().isoformat()))
    logger.info(f"回滚到 {old_hash}")

    try:
        # 1. git checkout 之前版本
        phase_logs.append(("rollback", "正在切换代码版本...", datetime.now().isoformat()))
        checkout = subprocess.run(
            ["git", "checkout", old_hash],
            capture_output=True, text=True, cwd=work_dir, timeout=60
        )
        if checkout.returncode != 0:
            raise RuntimeError(f"git checkout 失败: {checkout.stderr.strip()[:300]}")
        phase_logs.append(("rollback", "代码版本切换完成", datetime.now().isoformat()))

        # 2. 重新构建
        phase_logs.append(("rollback", "正在重新构建前端...", datetime.now().isoformat()))
        subprocess.run(
            ["npm", "ci"], capture_output=True, text=True,
            cwd=f"{work_dir}/frontend", timeout=120
        ).check_returncode()
        subprocess.run(
            ["npm", "run", "build"], capture_output=True, text=True,
            cwd=f"{work_dir}/frontend", timeout=180
        ).check_returncode()
        phase_logs.append(("rollback", "前端构建完成", datetime.now().isoformat()))

        phase_logs.append(("rollback", "正在重新构建后端...", datetime.now().isoformat()))
        subprocess.run(
            ["mvn", "clean", "package", "-DskipTests", "-B"], capture_output=True, text=True,
            cwd=f"{work_dir}/backend", timeout=300
        ).check_returncode()
        phase_logs.append(("rollback", "后端构建完成", datetime.now().isoformat()))

        phase_logs.append(("rollback", "正在构建 Docker 镜像...", datetime.now().isoformat()))
        subprocess.run(
            ["docker", "compose", "build"], capture_output=True, text=True,
            cwd=deploy_dir, timeout=600
        ).check_returncode()
        phase_logs.append(("rollback", "Docker 镜像构建完成", datetime.now().isoformat()))

        # 3. 重新部署
        phase_logs.append(("rollback", "正在重新部署...", datetime.now().isoformat()))
        subprocess.run(
            ["docker", "compose", "down", "--remove-orphans"],
            capture_output=True, text=True, cwd=deploy_dir, timeout=120
        )
        subprocess.run(
            ["docker", "compose", "up", "-d", "--build"],
            capture_output=True, text=True, cwd=deploy_dir, timeout=600
        ).check_returncode()
        phase_logs.append(("rollback", "部署完成", datetime.now().isoformat()))

        # 4. 验证
        phase_logs.append(("rollback", "正在验证服务...", datetime.now().isoformat()))
        time.sleep(10)  # 等待服务启动
        for _ in range(6):
            ps = subprocess.run(
                ["docker", "compose", "ps", "--status", "running", "--format", "json"],
                capture_output=True, text=True, cwd=deploy_dir, timeout=30
            )
            if "backend" in ps.stdout and "agent" in ps.stdout and "frontend" in ps.stdout:
                phase_logs.append(("rollback", "服务验证通过", datetime.now().isoformat()))
                break
            time.sleep(5)
        else:
            raise RuntimeError("回滚后服务未就绪")

        phase_status["rollback"] = "success"
        logger.info("回滚成功！")

        return {
            "current_phase": "rollback",
            "phase_status": phase_status,
            "phase_logs": phase_logs,
            "rollback_status": "success",
            "final_status": "rolled_back",
        }

    except Exception as e:
        error_msg = f"回滚失败: {e}"
        logger.error(error_msg)
        phase_logs.append(("rollback", error_msg, datetime.now().isoformat()))
        phase_status["rollback"] = "failed"
        return {
            "current_phase": "rollback",
            "phase_status": phase_status,
            "phase_logs": phase_logs,
            "rollback_status": "failed",
            "final_status": "failed",
            "error": error_msg,
        }
