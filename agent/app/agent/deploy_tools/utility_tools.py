"""实用工具 — 健康检查、日志读取、文件编辑等辅助工具"""

import asyncio
import subprocess
import time
from pathlib import Path

import httpx
from langchain_core.tools import tool
from loguru import logger

from app.config import config


@tool
async def health_check(url: str = "") -> str:
    """验证部署的服务是否正常运行

    对指定 URL 发送 HTTP GET 请求，检查服务是否可访问。
    部署完成后使用此工具验证服务健康状态。

    Args:
        url: 待检查的 URL，为空时使用配置的 base_url

    Returns:
        str: 健康检查结果，包含 HTTP 状态码和响应时间
    """
    target = url or config.deploy_base_url
    max_retries = 3

    for i in range(max_retries):
        try:
            t0 = time.time()
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(target, follow_redirects=True)
                elapsed = int((time.time() - t0) * 1000)

                if resp.status_code == 200:
                    return (
                        f"✅ {target} 正常响应 ({elapsed}ms)\n"
                        f"HTTP {resp.status_code}"
                    )
                else:
                    return (
                        f"⚠️ {target} 返回异常状态码 ({elapsed}ms)\n"
                        f"HTTP {resp.status_code}\n"
                        f"响应: {resp.text[:200]}"
                    )

        except Exception as e:
            if i < max_retries - 1:
                await asyncio.sleep(3)
            else:
                return f"❌ {target} 不可达（重试 {max_retries} 次后）: {e}"

    return f"❌ {target} 健康检查失败"


@tool
def read_log(source: str = "build") -> str:
    """读取构建或部署日志

    当构建失败时，使用此工具查看详细的错误日志以诊断问题。

    Args:
        source: 日志来源，可选值：
               - "build" 或 "npm": 前端构建日志
               - "maven" 或 "backend": 后端构建日志
               - "docker": Docker 构建日志
               默认为 "build"

    Returns:
        str: 日志内容（仅包含最近的相关输出，最多 2000 字符）
    """
    work_dir = config.deploy_work_dir

    # 尝试从构建输出文件读取
    log_paths = {
        "build": Path(f"{work_dir}/frontend/npm-build.log"),
        "npm": Path(f"{work_dir}/frontend/npm-build.log"),
        "maven": Path(f"{work_dir}/backend/target/maven-build.log"),
        "backend": Path(f"{work_dir}/backend/target/maven-build.log"),
        "docker": Path(f"{work_dir}/deploy/docker-build.log"),
    }

    log_file = log_paths.get(source)
    if log_file and log_file.exists():
        content = log_file.read_text(encoding="utf-8", errors="replace")
        # 截取最后 2000 字符（通常错误在末尾）
        return content[-2000:] if len(content) > 2000 else content

    # 没有日志文件，提示用户直接查看构建工具的输出
    return (
        f"未找到 {source} 的日志文件。\n"
        f"请直接查看构建工具的输出信息，或确认构建是否已执行。"
    )


@tool
def read_file(path: str) -> str:
    """读取项目中的源代码文件

    当需要检查代码定位构建错误或配置问题时使用此工具。

    Args:
        path: 相对于项目根目录的文件路径，如 "frontend/vite.config.ts"
              或 "backend/src/main/resources/application.yml"

    Returns:
        str: 文件内容（最多 2000 字符）。如果文件较大，仅返回首尾部分。
    """
    full_path = Path(config.deploy_work_dir) / path

    if not full_path.exists():
        return f"文件不存在: {path}"

    if not full_path.is_file():
        return f"路径不是文件: {path}"

    try:
        content = full_path.read_text(encoding="utf-8", errors="replace")
        if len(content) <= 2000:
            return content
        else:
            # 返回开头和结尾
            head = content[:1000]
            tail = content[-900:]
            return (
                f"⚠️ 文件较大 (共 {len(content)} 字符)，显示首尾部分：\n\n"
                f"--- 文件开头 (1000 字符) ---\n{head}\n\n"
                f"--- 文件结尾 (900 字符) ---\n{tail}"
            )
    except Exception as e:
        return f"读取文件失败: {e}"


@tool
def edit_file(path: str, old_string: str, new_string: str) -> str:
    """修改项目中的源代码文件

    当定位到构建错误后，使用此工具修复代码。
    采用精确字符串替换方式，不破坏文件其余部分。

    Args:
        path: 相对于项目根目录的文件路径，如 "frontend/src/main.ts"
        old_string: 需要被替换的旧字符串（必须精确匹配文件中内容）
        new_string: 替换后的新字符串

    Returns:
        str: 替换结果和修改后的 diff 摘要
    """
    full_path = Path(config.deploy_work_dir) / path

    if not full_path.exists():
        return f"文件不存在: {path}"

    try:
        content = full_path.read_text(encoding="utf-8", errors="replace")

        if old_string not in content:
            return (
                f"错误: 在 {path} 中未找到匹配的文本。\n"
                f"请检查 old_string 是否与文件中内容完全一致。"
            )

        count = content.count(old_string)
        if count > 1:
            return (
                f"错误: old_string 在文件中出现 {count} 次，无法确定替换目标。\n"
                f"请提供更多上下文使匹配唯一。"
            )

        new_content = content.replace(old_string, new_string)
        full_path.write_text(new_content, encoding="utf-8")

        # 生成 diff 摘要
        diff_lines = []
        old_lines = old_string.split("\n")
        new_lines = new_string.split("\n")
        diff_lines.append(f"--- {path} (old)")
        diff_lines.append(f"+++ {path} (new)")
        for line in old_lines:
            diff_lines.append(f"-{line}")
        for line in new_lines:
            diff_lines.append(f"+{line}")

        return f"✅ 已修改 {path}\n\n修改内容:\n" + "\n".join(diff_lines[:50])

    except Exception as e:
        return f"修改文件失败: {e}"


@tool
def run_command(command: str) -> str:
    """在项目根目录执行任意 shell 命令

    当需要安装依赖、运行脚本或执行其他操作时使用此工具。
    注意：此工具会直接在项目目录执行命令，请谨慎使用。

    Args:
        command: 要执行的 shell 命令，如 "npm install axios" 或 "ls -la"

    Returns:
        str: 命令执行的标准输出和标准错误（最多 2000 字符）
    """
    work_dir = config.deploy_work_dir
    try:
        logger.info(f"run_command: {command}")

        result = subprocess.run(
            command,
            capture_output=True, text=True,
            cwd=work_dir, timeout=120, shell=True
        )

        output_parts = []
        if result.stdout:
            output_parts.append(result.stdout.strip()[:1500])
        if result.stderr:
            output_parts.append(f"stderr:\n{result.stderr.strip()[:500]}")

        output = "\n".join(output_parts)

        if result.returncode == 0:
            return f"✅ 命令执行成功\n{output}" if output else "✅ 命令执行成功（无输出）"
        else:
            return f"❌ 命令执行失败 (exit code {result.returncode})\n{output}"

    except subprocess.TimeoutExpired:
        return "⚠️ 命令执行超时（超过 120 秒）"
    except Exception as e:
        return f"⚠️ 命令执行异常: {e}"
