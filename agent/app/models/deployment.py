"""部署相关数据模型"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ManualTriggerRequest(BaseModel):
    """手动触发部署请求"""
    branch: str = Field(default="main", description="目标分支")


class DeploymentSummary(BaseModel):
    """部署摘要（用于历史列表）"""
    deployment_id: str = Field(..., description="部署 ID")
    trigger_type: str = Field(..., description="触发方式: webhook / manual")
    target_branch: str = Field(..., description="目标分支")
    commit_hash: str = Field(..., description="部署的提交哈希")
    commit_message: str = Field(default="", description="提交信息")
    final_status: str = Field(..., description="最终状态: running / success / failed / rolled_back")
    current_phase: str = Field(..., description="当前阶段")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    duration_ms: int = Field(default=0, description="耗时毫秒")


class PhaseInfo(BaseModel):
    """阶段信息"""
    name: str = Field(..., description="阶段名称")
    status: str = Field(..., description="状态: pending / running / success / failed / skipped")
    started_at: Optional[str] = Field(None, description="开始时间")
    finished_at: Optional[str] = Field(None, description="结束时间")
    message: str = Field(default="", description="阶段消息")


class LogEntry(BaseModel):
    """日志条目"""
    phase: str = Field(..., description="所属阶段")
    message: str = Field(..., description="日志内容")
    timestamp: str = Field(..., description="时间戳")


class DeploymentDetail(BaseModel):
    """部署详情"""
    deployment_id: str = Field(..., description="部署 ID")
    trigger_type: str = Field(..., description="触发方式")
    target_branch: str = Field(..., description="目标分支")
    commit_hash: str = Field(..., description="当前提交哈希")
    previous_commit_hash: str = Field(..., description="前一提交哈希（用于回滚）")
    commit_message: str = Field(default="", description="提交信息")
    final_status: str = Field(..., description="最终状态")
    current_phase: str = Field(..., description="当前阶段")
    phases: List[PhaseInfo] = Field(default_factory=list, description="各阶段信息")
    build_results: Dict[str, Any] = Field(default_factory=dict, description="构建结果")
    verify_results: Dict[str, Any] = Field(default_factory=dict, description="验证结果")
    logs: List[LogEntry] = Field(default_factory=list, description="部署日志")
    error: str = Field(default="", description="错误信息")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    duration_ms: int = Field(default=0, description="耗时毫秒")


class WebhookPayload(BaseModel):
    """Webhook 负载（GitHub 兼容）"""
    ref: str = Field(default="", description="引用的分支")
    before: str = Field(default="", description="之前的提交哈希")
    after: str = Field(default="", description="之后的提交哈希")
    commits: List[Dict[str, Any]] = Field(default_factory=list, description="提交列表")
    repository: Optional[Dict[str, Any]] = Field(None, description="仓库信息")
    head_commit: Optional[Dict[str, Any]] = Field(None, description="最新提交")

    @property
    def is_push_to_main(self) -> bool:
        """是否为推送到 main 分支"""
        return self.ref in ("refs/heads/main", "refs/heads/master")

    @property
    def commit_message(self) -> str:
        """获取最新提交信息"""
        if self.head_commit:
            return self.head_commit.get("message", "")
        return ""

    @property
    def commit_hash(self) -> str:
        """获取最新提交哈希"""
        return self.after or ""
