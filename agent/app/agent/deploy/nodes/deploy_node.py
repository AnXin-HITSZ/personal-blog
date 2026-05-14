"""阶段四：部署发布节点"""

import subprocess
import time
from datetime import datetime
from typing import Dict, Any

from loguru import logger

from app.config import config
from ..state import DeploymentState


async def deploy_node(state: DeploymentState) -> Dict[str, Any]:
    """阶段四：部署发布

    1. docker compose down（停止旧容器）
    2. docker compose up -d --build（启动新容器）
    3. 等待服务健康
    """
    logger.info("=== 阶段四：部署发布 ===")

    phase_logs = list(state.get("phase_logs", []))
    phase_status = dict(state.get("phase_status", {}))
    deploy_dir = f"{config.deploy_work_dir}/deploy"

    try:
        # 1. 停止旧容器
        phase_logs.append(("deploy", "正在停止旧容器...", datetime.now().isoformat()))
        logger.info("执行 docker compose down...")

        # 捕获输出但不阻塞（忽略 down 阶段的错误）
        subprocess.run(
            ["docker", "compose", "down", "--remove-orphans"],
            capture_output=True, text=True, cwd=deploy_dir, timeout=120
        )
        phase_logs.append(("deploy", "旧容器已停止", datetime.now().isoformat()))

        # 2. 启动新容器
        phase_logs.append(("deploy", "正在启动新容器...", datetime.now().isoformat()))
        logger.info("执行 docker compose up -d --build...")

        t0 = time.time()
        up_result = subprocess.run(
            ["docker", "compose", "up", "-d", "--build"],
            capture_output=True, text=True, cwd=deploy_dir, timeout=600
        )

        if up_result.returncode != 0:
            stderr = up_result.stderr.strip()[:500]
            stdout = up_result.stdout.strip()[:500]
            raise RuntimeError(f"docker compose up 失败: {stderr} {stdout}")

        deploy_duration = int((time.time() - t0) * 1000)
        phase_logs.append(("deploy", f"容器启动完成 ({deploy_duration}ms)", datetime.now().isoformat()))

        # 3. 等待服务健康
        phase_logs.append(("deploy", "等待服务就绪...", datetime.now().isoformat()))
        logger.info("等待服务健康检查...")

        # 最多等待 60 秒，每 5 秒检查一次
        max_retries = config.deploy_health_check_retries
        interval = config.deploy_health_check_interval

        all_healthy = True
        for i in range(max_retries):
            time.sleep(interval)
            ps_result = subprocess.run(
                ["docker", "compose", "ps", "--status", "running", "--format", "json"],
                capture_output=True, text=True, cwd=deploy_dir, timeout=30
            )
            # 简单检查：至少 backend、agent、frontend 在运行
            running_services = ps_result.stdout.strip()
            if "backend" in running_services and "agent" in running_services and "frontend" in running_services:
                phase_logs.append(("deploy", f"服务已就绪（第 {i+1} 次检查）", datetime.now().isoformat()))
                all_healthy = True
                break
            logger.info(f"等待服务就绪... ({i+1}/{max_retries})")
            all_healthy = False

        if not all_healthy:
            # 收集失败的容器日志
            failed_logs = subprocess.run(
                ["docker", "compose", "ps"],
                capture_output=True, text=True, cwd=deploy_dir, timeout=30
            )
            raise RuntimeError(f"服务未在预期时间内就绪:\n{failed_logs.stdout.strip()[:500]}")

        phase_logs.append(("deploy", "所有服务已就绪", datetime.now().isoformat()))
        phase_status["deploy"] = "success"
        logger.info("部署完成，所有服务已就绪")

        return {
            "current_phase": "deploy",
            "phase_status": phase_status,
            "phase_logs": phase_logs,
        }

    except Exception as e:
        error_msg = f"部署失败: {e}"
        logger.error(error_msg)
        phase_logs.append(("deploy", error_msg, datetime.now().isoformat()))
        phase_status["deploy"] = "failed"
        return {
            "current_phase": "deploy",
            "phase_status": phase_status,
            "phase_logs": phase_logs,
            "needs_rollback": True,
            "error": error_msg,
        }
