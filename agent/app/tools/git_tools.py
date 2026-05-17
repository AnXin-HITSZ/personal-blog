"""Git 工具 - 从工作目录查询 Git 仓库信息"""

import os
import subprocess
from pathlib import Path
from typing import Optional

from langchain_core.tools import tool
from loguru import logger

# 项目根目录（Git 工作目录）
WORK_DIR = os.getenv("DEPLOY_WORK_DIR", str(Path(__file__).resolve().parent.parent.parent.parent))


def _git(*args: str, cwd: str = WORK_DIR) -> str:
    """执行 git 命令并返回输出"""
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=15,
        )
        if result.returncode != 0:
            return f"Git 错误: {result.stderr.strip()}"
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "Git 命令执行超时"
    except FileNotFoundError:
        return "未找到 git 命令，请确保 Git 已安装"
    except Exception as e:
        logger.error(f"Git 命令执行失败: {e}")
        return f"Git 命令执行失败: {e}"


@tool
def get_git_log(count: int = 10, branch: str = "") -> str:
    """查看最近的 Git 提交记录

    Args:
        count: 显示最近多少条提交（默认 10）
        branch: 分支名（可选，为空则使用当前分支）
    """
    try:
        branch_arg = branch if branch else "HEAD"
        output = _git(
            "log", f"-{count}", "--format=%h %s%n  作者: %an, %ar%n", branch_arg,
        )
        if output.startswith("Git 错误"):
            return output
        if not output:
            return "该分支没有提交记录"
        # 美化输出
        commits = output.strip().split("\n\n")
        lines = [f"📜 最近 {len(commits)} 条提交记录", f"仓库: {WORK_DIR}"]
        if branch:
            lines.append(f"分支: {branch}")
        lines.append("-" * 50)
        for c in commits:
            for line in c.strip().split("\n"):
                lines.append(f"  {line.strip()}")
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"get_git_log 失败: {e}")
        return f"获取提交记录失败: {e}"


@tool
def get_git_status() -> str:
    """查看当前 Git 工作树状态：修改、暂存、未跟踪文件"""
    output = _git("status", "--short")
    if output.startswith("Git 错误"):
        # 如果不是简短模式，尝试完整输出
        output = _git("status")

    branch = _git("branch", "--show-current")
    has_unmerged = _git("log", "--oneline", "HEAD..@{upstream}", "--")

    lines = [f"🌿 当前分支: {branch}", ""]
    if has_unmerged and not has_unmerged.startswith("Git 错误"):
        lines.append(f"⚠️  落后远程 {len(has_unmerged.split(chr(10)))} 个提交")
        lines.append("")

    if output.startswith("Git 错误"):
        return output

    if not output.strip():
        lines.append("✅ 工作区干净，没有未提交的变更")
    else:
        lines.append("变更状态:")
        for line in output.strip().split("\n"):
            if line.startswith("??"):
                lines.append(f"  ❓ {line[2:].strip()}  (未跟踪)")
            elif line.startswith("M "):
                lines.append(f"  📝 {line[2:].strip()}  (已暂存)")
            elif line.startswith(" M"):
                lines.append(f"  ✏️  {line[2:].strip()}  (未暂存)")
            elif line.startswith("A "):
                lines.append(f"  ✅ {line[2:].strip()}  (新增)")
            elif line.startswith("D"):
                lines.append(f"  🗑️  {line[2:].strip()}  (删除)")
            else:
                lines.append(f"  {line}")
    return "\n".join(lines)


@tool
def get_git_branch() -> str:
    """列出所有本地和远程分支"""
    local = _git("branch")
    if local.startswith("Git 错误"):
        return local

    lines = ["🌿 本地分支:"]
    for b in local.strip().split("\n"):
        b = b.strip()
        if b.startswith("*"):
            lines.append(f"  ✅ {b[1:].strip()}  (当前)")
        else:
            lines.append(f"     {b}")

    remote = _git("branch", "-r")
    if remote and not remote.startswith("Git 错误"):
        lines.append("")
        lines.append("🌐 远程分支:")
        for b in remote.strip().split("\n"):
            lines.append(f"     {b.strip()}")

    return "\n".join(lines)


@tool
def get_git_diff(target: str = "HEAD", path: str = "") -> str:
    """查看工作区与指定提交/分支的差异

    Args:
        target: 对比目标，可以是分支名、commit hash(如 HEAD~3) 或 HEAD。默认 HEAD
        path: 限定特定文件或目录（可选）
    """
    args = ["diff"]
    if target:
        args.append(target)
    if path:
        args.append("--", path)
    output = _git(*args)

    if output.startswith("Git 错误"):
        return output
    if not output.strip():
        return f"与 {target} 相比，没有差异"

    # 限制长度，diff 可能非常长
    if len(output) > 5000:
        output = output[:5000] + "\n\n... (输出过长已截断)"
    return output


@tool
def get_git_commit_detail(commit_hash: str) -> str:
    """查看某次提交的详细信息

    Args:
        commit_hash: 提交 hash（完整或短 hash）
    """
    output = _git(
        "show", commit_hash,
        "--format=%H%n作者: %an <%ae>%n日期: %ai%n%n%s%n%n%b",
        "--stat",
    )
    if output.startswith("Git 错误"):
        return output
    if not output.strip():
        return f"未找到提交: {commit_hash}"

    if len(output) > 3000:
        output = output[:3000] + "\n\n... (输出过长已截断)"
    return output
