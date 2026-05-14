"""Redis 客户端管理模块

使用 redis.asyncio 提供异步 Redis 连接管理，
遵循与 qdrant_client.py 相同的单例模式。
"""

from typing import Optional

from loguru import logger
from redis.asyncio import Redis as AsyncRedis

from app.config import config


class RedisClientManager:
    """Redis 客户端管理器（单例）"""

    def __init__(self) -> None:
        """初始化 Redis 客户端管理器"""
        self._client: Optional[AsyncRedis] = None

    async def connect(self) -> AsyncRedis:
        """
        连接到 Redis 服务器

        Returns:
            AsyncRedis: 异步 Redis 客户端实例

        Raises:
            RuntimeError: 连接失败时抛出
        """
        if self._client is not None:
            logger.debug("Redis 已连接，跳过重复 connect")
            return self._client

        try:
            logger.info(f"正在连接到 Redis: {config.redis_url}")

            self._client = AsyncRedis.from_url(
                config.redis_url,
                decode_responses=True,  # 自动解码 bytes → str
                socket_timeout=5,
                socket_connect_timeout=5,
            )

            # 验证连接
            await self._client.ping()
            logger.info("Redis 连接成功")

            return self._client

        except Exception as e:
            logger.error(f"Redis 连接失败: {e}")
            self._client = None
            raise RuntimeError(f"Redis 连接失败: {e}") from e

    async def get_client(self) -> AsyncRedis:
        """
        获取 Redis 客户端实例

        Returns:
            AsyncRedis: 异步 Redis 客户端

        Raises:
            RuntimeError: 客户端未初始化时抛出
        """
        if self._client is None:
            raise RuntimeError("Redis 客户端未初始化，请先调用 connect()")
        return self._client

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            bool: True 表示健康
        """
        try:
            if self._client is None:
                return False
            await self._client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis 健康检查失败: {e}")
            return False

    async def close(self) -> None:
        """关闭连接"""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.info("已关闭 Redis 连接")


# 全局单例
redis_manager = RedisClientManager()
