"""CI/CD 回顾工具 — 读取和写入 AGENTS.md 经验教训

供 CI/CD Agent 的 retrospective 节点和 executor 节点调用。
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path

from langchain_core.tools import tool
from loguru import logger

from app.config import config


def _agents_md_path() -> Path:
    """获取 AGENTS.md 的绝对路径（在 deploy_work_dir 中）"""
    return Path(config.deploy_work_dir) / "AGENTS.md"


@tool
def read_agents_md() -> str:
    """读取 AGENTS.md 中的历史 CI/CD 经验教训

    在部署执行过程中遇到问题时调用此工具，
    查看过去是否遇到过类似问题以及如何解决的。

    Returns:
        str: AGENTS.md 的完整内容，如果文件不存在则返回提示
    """
    path = _agents_md_path()
    if not path.exists():
        return "(暂无历史教训 — AGENTS.md 尚未创建)"

    try:
        content = path.read_text(encoding="utf-8")
        return content
    except Exception as e:
        logger.error(f"读取 AGENTS.md 失败: {e}")
        return f"(读取 AGENTS.md 失败: {e})"


@tool
def write_agents_lesson(
    problem: str,
    root_cause: str,
    prevention: str,
    impact: str = "",
) -> str:
    """将一次部署的经验教训写入 AGENTS.md 并提交到 git

    在部署完成后调用此工具，记录本次部署中遇到的问题和解决方案，
    以便未来的部署避免同样的错误。

    Args:
        problem: 出了什么问题（一句话描述）
        root_cause: 根本原因分析
        prevention: 下次如何预防（具体可操作的措施）
        impact: 造成的影响（可选，如"服务中断 5 分钟"）

    Returns:
        str: 操作结果描述
    """
    path = _agents_md_path()

    # 从环境变量获取部署 ID（executor 上下文中可能不可用）
    deployment_id = os.environ.get("CICD_DEPLOYMENT_ID", "unknown")
    final_status = os.environ.get("CICD_FINAL_STATUS", "unknown")

    date_str = datetime.now().strftime("%Y-%m-%d")
    entry = (
        f"\n"
        f"### {date_str} | {deployment_id} | {final_status}\n"
        f"- **问题**: {problem}\n"
        f"- **根因**: {root_cause}\n"
        f"- **预防**: {prevention}\n"
    )
    if impact:
        entry += f"- **影响**: {impact}\n"

    try:
        # 读取当前内容
        if path.exists():
            content = path.read_text(encoding="utf-8")
        else:
            content = _default_template()

        # 插入新教训（在第一个 "---" 分隔符之后追加）
        separator = "---\n"
        sep_idx = content.find(separator)
        if sep_idx != -1:
            insert_pos = sep_idx + len(separator)
            new_content = content[:insert_pos] + entry + content[insert_pos:]
        else:
            # 没有分隔符，直接追加
            new_content = content + "\n" + entry

        # 写入文件
        path.write_text(new_content, encoding="utf-8")
        logger.info(f"AGENTS.md 已追加新教训: {problem[:50]}")

        # git add + commit（不 push）
        try:
            work_dir = config.deploy_work_dir
            subprocess.run(
                ["git", "add", "AGENTS.md"],
                capture_output=True, text=True,
                cwd=work_dir, timeout=30,
            )
            commit_msg = f"docs: add deployment lesson from {deployment_id}"
            subprocess.run(
                ["git", "commit", "-m", commit_msg, "--allow-empty"],
                capture_output=True, text=True,
                cwd=work_dir, timeout=30,
            )
            logger.info(f"AGENTS.md 已提交: {commit_msg}")
        except Exception as e:
            logger.warning(f"git commit AGENTS.md 失败（可手动提交）: {e}")

        return f"✅ 经验教训已写入 AGENTS.md\n问题: {problem}\n预防: {prevention}"

    except Exception as e:
        logger.error(f"写入 AGENTS.md 失败: {e}")
        return f"❌ 写入 AGENTS.md 失败: {e}"


def _default_template() -> str:
    """创建默认的 AGENTS.md 模板"""
    return (
        "# AGENTS.md — CI/CD 经验教训库\n"
        "\n"
        "此文件由 CI/CD Agent 自动维护。每次部署完成后，Agent 总结经验教训并追加到此文件。\n"
        "下次部署前，Agent 读取此文件，避免重蹈覆辙。\n"
        "\n"
        "---\n"
        "\n"
        "## 历史教训\n"
        "\n"
        "<!-- 新教训将按时间倒序追加在此 -->\n"
    )
