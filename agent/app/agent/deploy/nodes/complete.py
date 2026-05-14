"""阶段六：完成收尾节点"""

import subprocess
from datetime import datetime
from typing import Dict, Any

from loguru import logger

from app.config import config
from ..state import DeploymentState


async def complete_node(state: DeploymentState) -> Dict[str, Any]:
    """阶段六：完成收尾

    1. 生成部署报告
    2. 记录发布成功信息
    3. 发送通知
    """
    logger.info("=== 阶段六：完成收尾 ===")

    phase_logs = list(state.get("phase_logs", []))
    phase_status = dict(state.get("phase_status", {}))
    deployment_id = state["deployment_id"]

    try:
        commit_hash = state.get("commit_hash", "")
        commit_message = state.get("commit_message", "")
        trigger_type = state.get("trigger_type", "")
        final_status = state.get("final_status", "success")
        needs_rollback = state.get("needs_rollback", False)
        rollback_status = state.get("rollback_status", "")

        # 确定最终状态
        if needs_rollback and rollback_status == "success":
            final_status = "rolled_back"
        elif needs_rollback:
            final_status = "failed"
        else:
            final_status = "success"

        # 生成报告
        report = _generate_report(state, final_status)
        phase_logs.append(("complete", f"部署报告已生成", datetime.now().isoformat()))

        # 记录部署摘要到 git tag（可选）
        if final_status == "success":
            try:
                tag_name = f"deploy-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                subprocess.run(
                    ["git", "tag", "-a", tag_name, "-m", f"Auto deploy: {commit_message}"],
                    capture_output=True, text=True,
                    cwd=config.deploy_work_dir, timeout=30
                )
                phase_logs.append(("complete", f"Git tag 已创建: {tag_name}", datetime.now().isoformat()))
            except Exception as e:
                logger.warning(f"创建 git tag 失败: {e}")

        phase_status["complete"] = "success"
        logger.info(f"部署完成，最终状态: {final_status}")

        return {
            "current_phase": "complete",
            "phase_status": phase_status,
            "phase_logs": phase_logs,
            "final_status": final_status,
            "final_report": report,
        }

    except Exception as e:
        error_msg = f"收尾阶段失败: {e}"
        logger.error(error_msg)
        phase_logs.append(("complete", error_msg, datetime.now().isoformat()))
        phase_status["complete"] = "failed"
        return {
            "current_phase": "complete",
            "phase_status": phase_status,
            "phase_logs": phase_logs,
        }


def _generate_report(state: DeploymentState, final_status: str) -> str:
    """生成部署报告"""
    lines = []
    lines.append("# 部署报告")
    lines.append("")
    lines.append(f"- **部署 ID**: {state.get('deployment_id', '')}")
    lines.append(f"- **触发方式**: {state.get('trigger_type', '')}")
    lines.append(f"- **目标分支**: {state.get('target_branch', '')}")
    lines.append(f"- **提交哈希**: {state.get('commit_hash', '')}")
    lines.append(f"- **提交信息**: {state.get('commit_message', '')}")
    lines.append(f"- **最终状态**: {final_status}")
    lines.append(f"- **完成时间**: {datetime.now().isoformat()}")
    lines.append("")

    # 阶段摘要
    phase_status = state.get("phase_status", {})
    lines.append("## 阶段状态")
    lines.append("")
    lines.append("| 阶段 | 状态 |")
    lines.append("|------|------|")
    for phase, status in phase_status.items():
        lines.append(f"| {phase} | {status} |")

    lines.append("")
    if state.get("error"):
        lines.append("## 错误信息")
        lines.append("")
        lines.append(f"```\n{state['error']}\n```")

    return "\n".join(lines)
