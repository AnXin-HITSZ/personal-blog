"""Git 操作工具 — 代码拉取与变更查看"""

import subprocess

from langchain_core.tools import tool
from loguru import logger

from app.config import config


@tool
def git_pull(branch: str = "main") -> str:
    """拉取指定分支的最新代码

    从远程仓库 fetch 并 pull 指定分支的更新。
    当需要获取最新代码进行部署时使用此工具。

    Args:
        branch: 目标分支名，默认为 main

    Returns:
        str: 操作结果描述，包含 commit hash 和变更信息
    """
    work_dir = config.deploy_work_dir
    try:
        logger.info(f"git_pull: 拉取 {branch} 分支")

        # fetch
        fetch = subprocess.run(
            ["git", "fetch", "origin", branch],
            capture_output=True, text=True, cwd=work_dir, timeout=60
        )
        if fetch.returncode != 0:
            return f"git fetch 失败: {fetch.stderr.strip()[:500]}"

        # 检查是否有新提交
        rev_count = subprocess.run(
            ["git", "rev-list", "--count", f"HEAD..origin/{branch}"],
            capture_output=True, text=True, cwd=work_dir, timeout=30
        )
        ahead = int(rev_count.stdout.strip() or "0")

        if ahead == 0:
            head_hash = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True, text=True, cwd=work_dir, timeout=30
            ).stdout.strip()
            return f"已是最新，无新提交。当前 HEAD: {head_hash}"

        # pull
        pull = subprocess.run(
            ["git", "pull", "origin", branch],
            capture_output=True, text=True, cwd=work_dir, timeout=120
        )
        if pull.returncode != 0:
            return f"git pull 失败: {pull.stderr.strip()[:500]}"

        # 检查冲突
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=work_dir, timeout=30
        )
        if "UU " in status.stdout or "AA " in status.stdout:
            return f"检测到合并冲突:\n{status.stdout.strip()[:500]}"

        # 获取新 hash
        new_hash = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, cwd=work_dir, timeout=30
        ).stdout.strip()

        commit_msg = subprocess.run(
            ["git", "log", "-1", "--pretty=format:%s"],
            capture_output=True, text=True, cwd=work_dir, timeout=30
        ).stdout.strip()

        return (
            f"✅ 拉取成功！更新了 {ahead} 个提交\n"
            f"当前 HEAD: {new_hash}\n"
            f"最新提交: {commit_msg}"
        )

    except subprocess.TimeoutExpired:
        return "⚠️ git 操作超时（超过 120 秒）"
    except Exception as e:
        return f"⚠️ git pull 异常: {e}"


@tool
def get_git_diff() -> str:
    """获取当前工作目录的 git diff 统计

    查看代码变更摘要。在部署前或修复代码后，
    用于了解哪些文件被修改以及修改的规模。

    Returns:
        str: git diff --stat 输出
    """
    work_dir = config.deploy_work_dir
    try:
        # --stat 简洁摘要
        stat = subprocess.run(
            ["git", "diff", "--stat"],
            capture_output=True, text=True, cwd=work_dir, timeout=30
        ).stdout.strip()

        # staged 变更
        staged = subprocess.run(
            ["git", "diff", "--stat", "--cached"],
            capture_output=True, text=True, cwd=work_dir, timeout=30
        ).stdout.strip()

        parts = []
        if stat:
            parts.append(f"未暂存的变更:\n{stat}")
        if staged:
            parts.append(f"已暂存的变更:\n{staged}")
        if not parts:
            return "当前无未提交的代码变更。"

        return "\n\n".join(parts)

    except Exception as e:
        return f"获取 git diff 失败: {e}"
