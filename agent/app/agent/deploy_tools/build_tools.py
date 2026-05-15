"""构建工具 — npm / Maven / Docker 构建与部署"""

import subprocess
import time

from langchain_core.tools import tool
from loguru import logger

from app.config import config


@tool
def npm_build() -> str:
    """构建前端项目

    在 frontend 目录下执行 npm ci 和 npm run build。
    当需要构建前端 SPA 时使用此工具。

    Returns:
        str: 构建日志输出，包含成功/失败信息及耗时
    """
    frontend_dir = f"{config.deploy_work_dir}/frontend"
    try:
        logger.info("npm_build: 开始前端构建")

        t0 = time.time()

        # npm ci（安装依赖）
        ci = subprocess.run(
            ["npm", "ci"],
            capture_output=True, text=True, cwd=frontend_dir, timeout=120
        )
        if ci.returncode != 0:
            return f"npm ci 失败:\n{ci.stderr.strip()[:1000]}"

        # npm run build
        build = subprocess.run(
            ["npm", "run", "build"],
            capture_output=True, text=True, cwd=frontend_dir, timeout=180
        )
        elapsed = int((time.time() - t0) * 1000)

        if build.returncode == 0:
            return f"✅ 前端构建成功 ({elapsed}ms)\n{build.stdout.strip()[:500]}"
        else:
            return (
                f"❌ 前端构建失败 ({elapsed}ms)\n"
                f"stdout:\n{build.stdout.strip()[:1000]}\n"
                f"stderr:\n{build.stderr.strip()[:1000]}"
            )

    except subprocess.TimeoutExpired:
        return "⚠️ 前端构建超时（超过 180 秒）"
    except Exception as e:
        return f"⚠️ 前端构建异常: {e}"


@tool
def maven_build() -> str:
    """构建后端项目

    在 backend 目录下执行 Maven 打包（跳过测试）。
    当需要构建 Spring Boot 后端 JAR 时使用此工具。

    Returns:
        str: 构建日志输出，包含成功/失败信息及耗时
    """
    backend_dir = f"{config.deploy_work_dir}/backend"
    try:
        logger.info("maven_build: 开始后端构建")

        t0 = time.time()
        mvn = subprocess.run(
            ["mvn", "clean", "package", "-DskipTests", "-B"],
            capture_output=True, text=True, cwd=backend_dir, timeout=300
        )
        elapsed = int((time.time() - t0) * 1000)

        if mvn.returncode == 0:
            return f"✅ 后端构建成功 ({elapsed}ms)\n{mvn.stdout.strip()[:500]}"
        else:
            return (
                f"❌ 后端构建失败 ({elapsed}ms)\n"
                f"stdout:\n{mvn.stdout.strip()[:1000]}\n"
                f"stderr:\n{mvn.stderr.strip()[:1000]}"
            )

    except subprocess.TimeoutExpired:
        return "⚠️ 后端构建超时（超过 300 秒）"
    except Exception as e:
        return f"⚠️ 后端构建异常: {e}"


@tool
def docker_build() -> str:
    """构建 Docker 镜像

    在 deploy 目录下执行 docker compose build 构建所有服务镜像。
    当需要在部署前构建或更新 Docker 镜像时使用此工具。

    Returns:
        str: 构建日志输出，包含成功/失败信息及耗时
    """
    deploy_dir = f"{config.deploy_work_dir}/deploy"
    try:
        logger.info("docker_build: 开始构建 Docker 镜像")

        t0 = time.time()
        build = subprocess.run(
            ["docker", "compose", "build"],
            capture_output=True, text=True, cwd=deploy_dir, timeout=600
        )
        elapsed = int((time.time() - t0) * 1000)

        if build.returncode == 0:
            return f"✅ Docker 镜像构建成功 ({elapsed}ms)\n{build.stdout.strip()[:500]}"
        else:
            return (
                f"❌ Docker 镜像构建失败 ({elapsed}ms)\n"
                f"stdout:\n{build.stdout.strip()[:1000]}\n"
                f"stderr:\n{build.stderr.strip()[:1000]}"
            )

    except subprocess.TimeoutExpired:
        return "⚠️ Docker 构建超时（超过 600 秒）"
    except Exception as e:
        return f"⚠️ Docker 构建异常: {e}"


@tool
def docker_deploy() -> str:
    """部署 Docker 容器

    停止旧容器并启动新容器，然后等待服务就绪。
    使用 docker compose down 停止旧容器，docker compose up -d 启动新容器。

    Returns:
        str: 部署日志，包含容器启动状态和服务健康状态
    """
    deploy_dir = f"{config.deploy_work_dir}/deploy"
    try:
        logger.info("docker_deploy: 开始部署")

        # down
        subprocess.run(
            ["docker", "compose", "down", "--remove-orphans"],
            capture_output=True, text=True, cwd=deploy_dir, timeout=120
        )

        # up -d
        t0 = time.time()
        up = subprocess.run(
            ["docker", "compose", "up", "-d", "--build"],
            capture_output=True, text=True, cwd=deploy_dir, timeout=600
        )
        elapsed = int((time.time() - t0) * 1000)

        if up.returncode != 0:
            return (
                f"❌ docker compose up 失败 ({elapsed}ms)\n"
                f"{up.stderr.strip()[:500]}\n{up.stdout.strip()[:500]}"
            )

        # 等待服务就绪
        max_retries = config.deploy_health_check_retries
        interval = config.deploy_health_check_interval

        for i in range(max_retries):
            time.sleep(interval)
            ps = subprocess.run(
                ["docker", "compose", "ps", "--status", "running", "--format", "json"],
                capture_output=True, text=True, cwd=deploy_dir, timeout=30
            )
            running = ps.stdout.strip()
            if "backend" in running and "agent" in running and "frontend" in running:
                return (
                    f"✅ 部署成功 ({elapsed}ms)\n"
                    f"服务已全部就绪（第 {i+1} 次健康检查通过）"
                )

        return "⚠️ 容器已启动但服务健康检查未全部通过，请手动验证"

    except subprocess.TimeoutExpired:
        return "⚠️ docker compose 操作超时"
    except Exception as e:
        return f"⚠️ 部署异常: {e}"
