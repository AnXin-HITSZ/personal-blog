"""阶段三：构建测试节点"""

import subprocess
import time
from datetime import datetime
from typing import Dict, Any

from loguru import logger

from app.config import config
from ..state import DeploymentState


async def build_test_node(state: DeploymentState) -> Dict[str, Any]:
    """阶段三：构建测试

    1. 前端构建: npm ci + npm run build
    2. 后端构建: mvn clean package -DskipTests
    3. Docker 镜像构建
    """
    logger.info("=== 阶段三：构建测试 ===")

    phase_logs = list(state.get("phase_logs", []))
    phase_status = dict(state.get("phase_status", {}))
    build_results = dict(state.get("build_results", {}))
    work_dir = config.deploy_work_dir

    try:
        # ─── 1. 前端构建 ───
        phase_logs.append(("build_test", "开始前端构建...", datetime.now().isoformat()))
        logger.info("构建前端...")

        frontend_dir = f"{work_dir}/frontend"
        t0 = time.time()

        # npm ci
        npm_ci = subprocess.run(
            ["npm", "ci"],
            capture_output=True, text=True, cwd=frontend_dir, timeout=120
        )
        if npm_ci.returncode != 0:
            raise RuntimeError(f"npm ci 失败: {npm_ci.stderr.strip()[:500]}")

        # npm run build
        npm_build = subprocess.run(
            ["npm", "run", "build"],
            capture_output=True, text=True, cwd=frontend_dir, timeout=180
        )
        if npm_build.returncode != 0:
            raise RuntimeError(f"npm run build 失败: {npm_build.stderr.strip()[:500]}")

        frontend_duration = int((time.time() - t0) * 1000)
        phase_logs.append(("build_test", f"前端构建完成 ({frontend_duration}ms)", datetime.now().isoformat()))
        build_results["frontend"] = {
            "success": True,
            "duration_ms": frontend_duration,
        }
        logger.info(f"前端构建完成: {frontend_duration}ms")

        # ─── 2. 后端构建 ───
        phase_logs.append(("build_test", "开始后端构建...", datetime.now().isoformat()))
        logger.info("构建后端...")

        backend_dir = f"{work_dir}/backend"
        t0 = time.time()

        maven_build = subprocess.run(
            ["mvn", "clean", "package", "-DskipTests", "-B"],
            capture_output=True, text=True, cwd=backend_dir, timeout=300
        )
        if maven_build.returncode != 0:
            raise RuntimeError(f"Maven 构建失败: {maven_build.stderr.strip()[:500]}")

        backend_duration = int((time.time() - t0) * 1000)
        phase_logs.append(("build_test", f"后端构建完成 ({backend_duration}ms)", datetime.now().isoformat()))
        build_results["backend"] = {
            "success": True,
            "duration_ms": backend_duration,
        }
        logger.info(f"后端构建完成: {backend_duration}ms")

        # ─── 3. Docker 镜像构建 ───
        phase_logs.append(("build_test", "开始构建 Docker 镜像...", datetime.now().isoformat()))
        logger.info("构建 Docker 镜像...")

        deploy_dir = f"{work_dir}/deploy"
        t0 = time.time()

        docker_build = subprocess.run(
            ["docker", "compose", "build"],
            capture_output=True, text=True, cwd=deploy_dir, timeout=600
        )
        if docker_build.returncode != 0:
            raise RuntimeError(f"Docker 构建失败: {docker_build.stderr.strip()[:500]}")

        docker_duration = int((time.time() - t0) * 1000)
        phase_logs.append(("build_test", f"Docker 镜像构建完成 ({docker_duration}ms)", datetime.now().isoformat()))
        build_results["docker"] = {
            "success": True,
            "duration_ms": docker_duration,
        }
        logger.info(f"Docker 构建完成: {docker_duration}ms")

        phase_status["build_test"] = "success"

        return {
            "current_phase": "build_test",
            "phase_status": phase_status,
            "phase_logs": phase_logs,
            "build_results": build_results,
        }

    except subprocess.TimeoutExpired as e:
        error_msg = f"构建超时: {e}"
        logger.error(error_msg)
        phase_logs.append(("build_test", error_msg, datetime.now().isoformat()))
        phase_status["build_test"] = "failed"
        return {
            "current_phase": "build_test",
            "phase_status": phase_status,
            "phase_logs": phase_logs,
            "build_results": build_results,
            "needs_rollback": True,
            "error": error_msg,
        }
    except Exception as e:
        error_msg = f"构建失败: {e}"
        logger.error(error_msg)
        phase_logs.append(("build_test", error_msg, datetime.now().isoformat()))
        phase_status["build_test"] = "failed"
        return {
            "current_phase": "build_test",
            "phase_status": phase_status,
            "phase_logs": phase_logs,
            "build_results": build_results,
            "needs_rollback": True,
            "error": error_msg,
        }
