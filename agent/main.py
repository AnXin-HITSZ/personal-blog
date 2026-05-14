"""FastAPI Agent 服务入口

作为个人博客的 AI Agent 微服务，提供 RAG 知识库管理、
语义搜索等能力。通过 Nginx 与 Spring Boot 后端集成。
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import config
from app.api import file, rag, chat, deployment


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("=" * 60)
    logger.info(f"Agent 服务启动中... v{config.app_version}")
    logger.info(f"环境: {'开发' if config.debug else '生产'}")
    logger.info(f"监听: http://{config.host}:{config.port}")

    # 连接 Qdrant
    from app.core.qdrant_client import qdrant_manager
    logger.info("连接 Qdrant...")
    try:
        qdrant_manager.connect()
        logger.info("Qdrant 连接成功")
    except Exception as e:
        logger.error(f"Qdrant 连接失败: {e}")
        logger.warning("向量数据库不可用，部分功能将受限")

    # 连接 Redis
    from app.core.redis_client import redis_manager
    logger.info("连接 Redis...")
    try:
        await redis_manager.connect()
        logger.info("Redis 连接成功")
    except Exception as e:
        logger.error(f"Redis 连接失败: {e}")
        logger.warning("Redis 不可用，对话历史将不会持久化")

    logger.info("=" * 60)

    yield

    logger.info("关闭 Qdrant 连接...")
    qdrant_manager.close()
    logger.info("关闭 Redis 连接...")
    await redis_manager.close()
    logger.info("Agent 服务已关闭")


app = FastAPI(
    title="AnXin Blog - Agent Service",
    version=config.app_version,
    description="个人博客 AI Agent 服务 — RAG 知识库与语义搜索",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(file.router, prefix="/api/agent", tags=["文件管理"])
app.include_router(rag.router, prefix="/api/agent", tags=["RAG 搜索"])
app.include_router(chat.router, prefix="/api/agent", tags=["对话"])
app.include_router(deployment.router, prefix="/api/agent", tags=["部署"])


@app.get("/api/agent/health")
async def health_check():
    """健康检查"""
    from app.core.qdrant_client import qdrant_manager
    return {
        "status": "ok",
        "version": config.app_version,
        "qdrant_connected": qdrant_manager.health_check(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level="info",
    )
