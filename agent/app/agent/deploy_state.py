"""
Agent 驱动 CI/CD 的共享状态定义

扩展自 PlanExecuteState，增加部署专用字段
"""

from typing import Dict, List, TypedDict, Annotated, Any
import operator


class CICDState(TypedDict):
    """Agent 驱动 CI/CD 状态

    与 PlanExecuteState 兼容的核心字段：
    - input / plan / past_steps / response
    同时保持与原有 DeploymentService 前端兼容：
    - phase_status / phase_logs / build_results / verify_results
    """

    # ── 继承 PlanExecuteState 的结构 ──
    input: str                              # 部署请求（如 "deploy main branch"）
    plan: List[str]                         # LLM 生成的计划步骤
    past_steps: Annotated[List[tuple], operator.add]  # [(步骤描述, 执行结果), ...]
    response: str                           # 最终部署报告

    # ── 部署标识 ──
    deployment_id: str                      # deploy-{timestamp}-{uuid}
    trigger_type: str                       # webhook / manual
    target_branch: str                      # 目标分支（默认 main）

    # ── Git 信息 ──
    commit_hash: str                        # 当前部署的提交哈希
    previous_commit_hash: str               # 部署前的 HEAD（用于回滚）
    commit_message: str                     # 提交信息

    # ── 部署状态（前端兼容） ──
    final_status: str                       # running / success / failed / cancelled
    current_phase: str                      # 当前阶段标记
    phase_status: Dict[str, str]            # 阶段 → pending/running/success/failed/skipped
    phase_logs: Annotated[List[tuple], operator.add]  # [(phase, msg, ts), ...]

    # ── 构建与验证结果（前端兼容） ──
    build_results: Dict[str, Any]           # 构建结果
    verify_results: Dict[str, Any]          # 验证结果

    # ── 自修复记录 ──
    fix_attempts: int                       # 当前步骤修复尝试次数（上限 2）
    max_retries: int                        # 最大重试次数（默认 2）
    error_log: str                          # 当前错误日志快照

    # ── 审批状态 ──
    needs_approval: bool                    # 部署前是否需要审批
    approval_granted: bool                  # 审批是否通过
    pending_diff: str                       # 待审批的 git diff

    # ── 反馈回路 ──
    lessons_loaded: str                     # init_deploy 从 AGENTS.md 读取的历史教训文本
    start_time: str                         # 部署开始时间（ISO 格式），用于 retrospective 计算耗时
