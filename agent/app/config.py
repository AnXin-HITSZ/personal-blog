"""配置管理模块

使用 Pydantic Settings 实现类型安全的配置管理
"""

from typing import Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用配置
    app_name: str = "SuperBizAgent"
    app_version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 9900

    # DashScope 配置（仅用于 Embedding，保留不动）
    dashscope_api_key: str = ""
    dashscope_embedding_model: str = "text-embedding-v4"  # v4 支持多种维度（默认 1024）

    # DeepSeek 配置（OpenAI 兼容接口，用于 LLM 对话）
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # Qdrant 配置
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "biz"

    # RAG 配置
    rag_top_k: int = 3               # 默认检索数量（未使用重排时的 fallback）
    rag_model: str = "deepseek-chat"  # DeepSeek 对话模型

    # RAG 重排配置（先召回后重排）
    rag_rerank_top_n: int = 15       # 第一阶段召回数量
    rag_final_top_k: int = 3         # 重排后保留数量
    rag_rerank_model: str = "BAAI/bge-reranker-v2-m3"
    rag_rerank_model_path: str = ".model_cache/BAAI/bge-reranker-v2-m3"
    rag_rerank_device: str = "cpu"
    rag_rerank_use_fp16: bool = False

    # 文档分块配置
    chunk_max_size: int = 800
    chunk_overlap: int = 100

    # Redis 配置（对话记忆持久化）
    redis_url: str = "redis://localhost:6379/0"

    # MCP 服务配置
    mcp_cls_transport: str = "streamable-http"
    mcp_cls_url: str = "http://localhost:8003/mcp"
    mcp_monitor_transport: str = "streamable-http"
    mcp_monitor_url: str = "http://localhost:8004/mcp"

    # ─── 部署配置 ───
    deploy_work_dir: str = "/data/deploy"              # Git 工作目录
    deploy_repo_url: str = ""                           # 仓库地址
    deploy_default_branch: str = "main"                 # 默认分支
    deploy_webhook_secret: str = ""                     # Webhook 密钥
    deploy_notification_email: str = ""                 # 通知邮箱
    deploy_health_check_retries: int = 6                # 健康检查重试次数
    deploy_health_check_interval: int = 10              # 健康检查间隔（秒）
    deploy_base_url: str = "http://localhost"           # 验证阶段基础 URL（Docker 用 80，本地可用 8000）

    @property
    def mcp_servers(self) -> Dict[str, Dict[str, Any]]:
        """获取完整的 MCP 服务器配置"""
        return {
            "cls": {
                "transport": self.mcp_cls_transport,
                "url": self.mcp_cls_url,
            },
            "monitor": {
                "transport": self.mcp_monitor_transport,
                "url": self.mcp_monitor_url,
            }
        }


# 全局配置实例
config = Settings()
