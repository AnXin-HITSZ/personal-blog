"""部署状态定义"""

from typing import Dict, List, TypedDict, Annotated, Any
import operator


class DeploymentState(TypedDict):
    """部署流水线状态"""

    # ─── 基本信息 ───
    deployment_id: str                          # 部署 ID
    trigger_type: str                           # 触发方式: webhook / manual
    trigger_data: Dict[str, Any]               # 触发来源数据

    # ─── Git 信息 ───
    target_branch: str                          # 目标分支
    commit_hash: str                            # 当前部署的提交哈希
    previous_commit_hash: str                   # 部署前的提交哈希（用于回滚）
    commit_message: str                         # 提交信息

    # ─── 阶段状态 ───
    current_phase: str                          # 当前阶段名称
    phase_status: Dict[str, str]               # 阶段 -> pending/running/success/failed/skipped
    phase_logs: Annotated[List[tuple], operator.add]  # [(phase, message, timestamp), ...]

    # ─── 构建结果 ───
    build_results: Dict[str, Any]              # 构建输出

    # ─── 验证结果 ───
    verify_results: Dict[str, Any]             # 验证结果

    # ─── 回滚 ───
    needs_rollback: bool                        # 是否需要回滚
    rollback_status: str                        # pending/running/success/failed
    rollback_reason: str                        # 回滚原因

    # ─── 最终状态 ───
    final_status: str                           # running/success/failed/rolled_back
    final_report: str                           # 最终报告
    error: str                                  # 错误信息
