"""容器诊断工具集 — 供 CI/CD Agent 在部署失败时排查容器问题

设计原则：
- 不依赖 curl、wget、netstat、ss 等外部命令，全部用 Python 标准库实现
- 每个工具返回结构化的诊断结果，包含关键状态信息
- 所有命令在 deploy_work_dir 下执行（即项目根目录内的 deploy/ 目录）
"""

import subprocess
from pathlib import Path
from typing import Optional

from langchain_core.tools import tool
from loguru import logger

from app.config import config


@tool
def docker_ps(service: str = "") -> str:
    """查看 Docker 容器的运行状态

    使用 docker compose ps 检查各服务的状态（Up/Exited/Healthy）。
    当部署后服务不可用时，先使用此工具了解整体状态。

    Args:
        service: 服务名称（如 backend/agent/frontend/mysql/redis/qdrant），
                 为空时返回所有服务状态

    Returns:
        str: 容器状态列表，包含名称、状态、端口映射等信息
    """
    deploy_dir = f"{config.deploy_work_dir}/deploy"
    try:
        cmd = ["docker", "compose", "ps"]
        if service:
            cmd.append(service)

        result = subprocess.run(
            cmd,
            capture_output=True, text=True, cwd=deploy_dir, timeout=30,
        )

        if result.returncode == 0 and result.stdout.strip():
            return f"📋 容器状态:\n{result.stdout.strip()}"
        elif result.returncode == 0:
            return "📋 容器状态: 无运行中的容器"
        else:
            return f"❌ docker compose ps 失败:\n{result.stderr.strip()[:500]}"

    except subprocess.TimeoutExpired:
        return "⚠️ docker compose ps 超时"
    except FileNotFoundError:
        return "⚠️ docker 命令不存在，请确认 Docker 已安装"
    except Exception as e:
        return f"⚠️ 诊断异常: {e}"


@tool
def docker_logs(service: str = "", tail: int = 50) -> str:
    """查看 Docker 容器的日志

    当 docker_ps 显示服务异常时，使用此工具查看详细日志定位原因。

    Args:
        service: 服务名称（如 backend/agent/frontend），为空时查看所有服务
        tail: 显示最近多少行日志，默认 50，最大 200

    Returns:
        str: 最近 N 行日志内容
    """
    tail = min(tail, 200)  # 防止日志过多
    deploy_dir = f"{config.deploy_work_dir}/deploy"
    try:
        cmd = ["docker", "compose", "logs", "--tail", str(tail), "--no-color"]
        if service:
            cmd.append(service)

        result = subprocess.run(
            cmd,
            capture_output=True, text=True, cwd=deploy_dir, timeout=30,
        )

        if result.returncode == 0 and result.stdout.strip():
            label = f"服务 {service}" if service else "所有服务"
            return f"📋 {label} 最近 {tail} 行日志:\n{result.stdout.strip()[-3000:]}"
        else:
            return f"⚠️ 日志为空或服务未运行:\n{result.stderr.strip()[:300]}"

    except subprocess.TimeoutExpired:
        return "⚠️ 获取日志超时"
    except Exception as e:
        return f"⚠️ 获取日志异常: {e}"


@tool
def check_port(service: str = "", port: int = 0) -> str:
    """检查容器内端口是否在监听

    使用容器内的 Python 或 /proc/net/tcp 检查端口开放状态。
    当服务无法访问时，先确认端口是否已成功监听。

    Args:
        service: 服务名称（如 backend/agent/frontend）
        port: 端口号（如 8000/8080/80/3306/6379/6333）

    Returns:
        str: 端口状态信息（是否开放、监听地址等）
    """
    if not service or not port:
        return "⚠️ 请指定 service 和 port 参数"

    deploy_dir = f"{config.deploy_work_dir}/deploy"
    hex_port = f"{port:04X}"  # 转为十六进制，如 8000 → 1F40

    try:
        # 法一：用 Python socket 检查（不需要容器内有 curl/ss）
        python_check = (
            f"python3 -c "
            f"\"import socket;s=socket.socket();s.settimeout(5);"
            f"s.connect(('localhost',{port}));print('OPEN');s.close()\""
            f" 2>/dev/null || "
            f"python -c "
            f"\"import socket;s=socket.socket();s.settimeout(5);"
            f"s.connect(('localhost',{port}));print('OPEN');s.close()\""
            f" 2>/dev/null"
        )

        cmd = [
            "docker", "compose", "exec", service,
            "sh", "-c", python_check,
        ]
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, cwd=deploy_dir, timeout=15,
        )

        if "OPEN" in result.stdout:
            return f"✅ 端口 {port} 在 {service} 容器内已开放（localhost:{port}）"

        # 法二：尝试通过 /proc/net/tcp 查看（兜底）
        proc_net_cmd = [
            "docker", "compose", "exec", service,
            "sh", "-c",
            "cat /proc/net/tcp 2>/dev/null",
        ]
        proc_result = subprocess.run(
            proc_net_cmd,
            capture_output=True, text=True, cwd=deploy_dir, timeout=10,
        )

        if proc_result.returncode == 0 and proc_result.stdout.strip():
            lines = proc_result.stdout.strip().split("\n")
            listening = []
            for line in lines[1:]:  # 跳过标题行
                parts = line.strip().split()
                if len(parts) >= 4 and parts[3] == "0A":  # 0A = LISTEN
                    local_addr = parts[1]
                    addr, p = local_addr.split(":")
                    listening.append(f"  地址 {addr} 端口 {int(p, 16)} (0x{p})")

            if listening:
                result_text = "\n".join(listening)
                port_listen = [l for l in listening if f"端口 {port}" in l or f"0x{hex_port}" in l]
                if port_listen:
                    return f"✅ 端口 {port} 正在监听:\n" + "\n".join(port_listen)
                return (
                    f"⚠️ 端口 {port} 未监听。容器内当前监听的端口:\n{result_text}\n\n"
                    f"💡 服务可能尚未就绪，请用 docker_logs 查看日志"
                )
            else:
                return f"❌ 端口 {port} 未监听，且容器内无任何端口开放"

        return (
            f"❌ 端口 {port} 在 {service} 容器内无法连接。\n"
            f"可能原因: 服务未启动 / 启动参数错误 / 进程崩溃"
        )

    except subprocess.TimeoutExpired:
        return "⚠️ 端口检查超时"
    except subprocess.CalledProcessError as e:
        return f"⚠️ 端口检查失败: {e.stderr.strip()[:300]}"
    except Exception as e:
        return f"⚠️ 端口检查异常: {e}"


@tool
def http_get(url: str, timeout: int = 10) -> str:
    """向指定 URL 发送 HTTP GET 请求检查服务响应

    使用 Python 标准库 urllib 实现，不依赖 curl/wget。
    当需要验证服务是否正常响应时使用此工具。

    Args:
        url: 完整 URL，如 http://backend:8080/api/agent/health
        timeout: 超时秒数，默认 10，最大 30

    Returns:
        str: HTTP 响应状态码、响应体和耗时
    """
    import time
    import urllib.request
    import urllib.error

    timeout = min(timeout, 30)
    try:
        t0 = time.time()
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = int((time.time() - t0) * 1000)
            body = resp.read().decode("utf-8", errors="replace")[:500]

            return (
                f"✅ {url}\n"
                f"  HTTP {resp.status} ({elapsed}ms)\n"
                f"  响应: {body}"
            )

    except urllib.error.HTTPError as e:
        elapsed = int((time.time() - t0) * 1000)
        body = e.read().decode("utf-8", errors="replace")[:300] if e.fp else ""
        return (
            f"⚠️ {url}\n"
            f"  HTTP {e.code} ({elapsed}ms)\n"
            f"  响应: {body}"
        )
    except urllib.error.URLError as e:
        return f"❌ {url}\n  连接失败: {e.reason}"
    except Exception as e:
        return f"❌ {url}\n  请求异常: {e}"


@tool
def container_env(service: str) -> str:
    """查看 Docker 容器的环境变量

    当服务配置可疑时，检查容器内环境变量是否正确设置。
    如 QDRANT_URL、DATABASE_URL 等连接信息是否指向正确的地址。

    Args:
        service: 服务名称（如 backend/agent/frontend）

    Returns:
        str: 环境变量列表（过滤掉 PATH 等无关变量，仅显示应用相关变量）
    """
    deploy_dir = f"{config.deploy_work_dir}/deploy"
    try:
        # 只显示应用关心的环境变量（排除系统变量）
        cmd = [
            "docker", "compose", "exec", service,
            "sh", "-c",
            "env | grep -E '^(QDRANT_|REDIS_|LLM_|DASHSCOPE_|JWT_|DB_|MYSQL_|DEPLOY_|INTERNAL_|SPRING_|JAVA_)' "
            "|| echo 'NO_MATCH'",
        ]
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, cwd=deploy_dir, timeout=15,
        )

        if result.returncode == 0 and result.stdout.strip():
            if "NO_MATCH" in result.stdout:
                # 没有匹配的应用环境变量，显示全部（排除过长值）
                return _get_all_env(service, deploy_dir)
            return f"📋 {service} 容器环境变量:\n{result.stdout.strip()}"
        else:
            return _get_all_env(service, deploy_dir)

    except subprocess.TimeoutExpired:
        return "⚠️ 获取环境变量超时"
    except Exception as e:
        return f"⚠️ 获取环境变量异常: {e}"


def _get_all_env(service: str, deploy_dir: str) -> str:
    """兜底：获取完整的 env 列表并截取"""
    try:
        cmd = ["docker", "compose", "exec", service, "sh", "-c", "env"]
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=deploy_dir, timeout=15,
        )
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split("\n")
            # 过滤掉过长值和系统 PATH 类变量
            filtered = [
                l for l in lines
                if len(l) < 200 and not l.startswith(("PATH=", "HOME=", "TERM=",
                                                       "HOSTNAME=", "PWD=", "SHLVL="))
            ]
            return f"📋 {service} 环境变量:\n" + "\n".join(filtered)
        return f"⚠️ 无法获取 {service} 的环境变量"
    except Exception:
        return f"⚠️ 无法获取 {service} 的环境变量"


@tool
def container_exec(service: str, command: str) -> str:
    """在指定 Docker 容器内执行诊断命令

    当需要更深入的排查时，在容器内执行特定命令。
    支持 Python 单行诊断、shell 命令等。
    注意：此工具会直接在容器内执行命令，请谨慎使用。

    Args:
        service: 服务名称（如 backend/agent/frontend/mysql/redis）
        command: 要执行的命令，如：
                - "python -c 'import socket;s=socket.socket();s.connect((\"localhost\",6379));print(\"OK\")'"
                - "cat /proc/net/tcp"
                - "env | grep QDRANT"
                - "ls -la /app/.model_cache/"

    Returns:
        str: 命令执行输出（最多 2000 字符）
    """
    deploy_dir = f"{config.deploy_work_dir}/deploy"
    try:
        result = subprocess.run(
            ["docker", "compose", "exec", service, "sh", "-c", command],
            capture_output=True, text=True, cwd=deploy_dir, timeout=30,
        )

        output_parts = []
        if result.stdout.strip():
            output_parts.append(result.stdout.strip()[:1500])
        if result.stderr.strip():
            output_parts.append(f"stderr:\n{result.stderr.strip()[:500]}")

        output = "\n".join(output_parts) if output_parts else "(无输出)"

        if result.returncode == 0:
            return f"✅ 命令执行成功:\n{output}"
        else:
            return f"⚠️ 命令退出码 {result.returncode}:\n{output}"

    except subprocess.TimeoutExpired:
        return "⚠️ 命令执行超时（超过 30 秒）"
    except Exception as e:
        return f"⚠️ 命令执行异常: {e}"


@tool
def network_connectivity(source_service: str, target_host: str, target_port: int) -> str:
    """测试容器间的网络连通性

    使用 Python 标准库 telnet 风格的 socket 连接测试，
    不依赖 ping/telnet/nc 等外部命令。
    当多个服务间调用失败时，排查网络连通性问题。

    Args:
        source_service: 发起测试的源服务名称（如 frontend/agent/backend）
        target_host: 目标主机名（服务名，如 mysql/redis/qdrant/backend/agent）
        target_port: 目标端口

    Returns:
        str: 连通性测试结果（成功/失败、延迟等）
    """
    deploy_dir = f"{config.deploy_work_dir}/deploy"
    try:
        python_code = (
            f"import socket,time;"
            f"s=socket.socket();"
            f"s.settimeout(5);"
            f"t0=time.time();"
            f"try:"
            f" s.connect(('{target_host}',{target_port}));"
            f" elapsed=int((time.time()-t0)*1000);"
            f" print(f'CONNECTED {{elapsed}}ms');"
            f" s.close();"
            f"except Exception as e:"
            f" print(f'FAILED {{e}}')"
        )

        cmd = [
            "docker", "compose", "exec", source_service,
            "python3", "-c", python_code,
        ]
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, cwd=deploy_dir, timeout=15,
        )

        if "CONNECTED" in result.stdout:
            elapsed = result.stdout.strip().replace("CONNECTED ", "")
            return (
                f"✅ {source_service} → {target_host}:{target_port} 连通 ({elapsed})"
            )
        elif "FAILED" in result.stdout:
            error = result.stdout.strip().replace("FAILED ", "")
            return (
                f"❌ {source_service} → {target_host}:{target_port} 不通\n"
                f"   错误: {error}\n"
                f"   💡 检查: 1) 目标服务是否运行 2) 服务名是否正确 3) 端口是否正确"
            )
        else:
            # 容器可能没有 Python3，尝试 python
            cmd[5] = "python"
            result2 = subprocess.run(
                cmd, capture_output=True, text=True, cwd=deploy_dir, timeout=15,
            )
            if "CONNECTED" in result2.stdout:
                elapsed = result2.stdout.strip().replace("CONNECTED ", "")
                return f"✅ {source_service} → {target_host}:{target_port} 连通 ({elapsed})"
            elif result2.stderr and "not found" in result2.stderr:
                return (
                    f"⚠️ {source_service} 容器内没有 Python。\n"
                    f"替代方案: 使用 container_exec 手动诊断"
                )
            else:
                error = result2.stdout.strip().replace("FAILED ", "")
                return f"❌ {source_service} → {target_host}:{target_port} 不通\n   错误: {error}"

    except subprocess.TimeoutExpired:
        return "⚠️ 连通性测试超时"
    except Exception as e:
        return f"⚠️ 连通性测试异常: {e}"


@tool
def check_disk_and_memory() -> str:
    """检查宿主机的磁盘和内存使用情况

    当服务启动失败或运行异常时，排查是否因资源不足导致。
    包括内存使用率、磁盘使用率、Docker 资源限制等。

    Returns:
        str: 系统资源使用情况
    """
    work_dir = config.deploy_work_dir
    try:
        parts = []

        # 磁盘使用
        df_result = subprocess.run(
            ["df", "-h", work_dir, "/"],
            capture_output=True, text=True, timeout=15,
        )
        if df_result.returncode == 0:
            parts.append(f"📀 磁盘使用:\n{df_result.stdout.strip()}")

        # 内存使用
        mem_result = subprocess.run(
            ["free", "-h"],
            capture_output=True, text=True, timeout=15,
        )
        if mem_result.returncode == 0:
            parts.append(f"🧠 内存使用:\n{mem_result.stdout.strip()}")

        # Docker 资源限制
        deploy_dir = f"{work_dir}/deploy"
        stats = subprocess.run(
            ["docker", "compose", "ps", "--format", "table {{.Name}}\t{{.Status}}\t{{.Ports}}"],
            capture_output=True, text=True, cwd=deploy_dir, timeout=15,
        )
        if stats.returncode == 0:
            parts.append(f"🐳 容器概览:\n{stats.stdout.strip()}")

        return "\n\n".join(parts) if parts else "⚠️ 无法获取系统资源信息"

    except subprocess.TimeoutExpired:
        return "⚠️ 资源检查超时"
    except Exception as e:
        return f"⚠️ 资源检查异常: {e}"
