"""Qdrant 客户端管理模块"""

from loguru import logger
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import (
    Distance,
    VectorParams,
    CollectionStatus,
)

from app.config import config


class QdrantClientManager:
    """Qdrant 客户端管理器"""

    COLLECTION_NAME: str = "biz"
    VECTOR_DIM: int = 1024

    def __init__(self) -> None:
        """初始化 Qdrant 客户端管理器"""
        self._client: QdrantClient | None = None

    def connect(self) -> QdrantClient:
        """
        连接到 Qdrant 服务器并初始化 collection

        Returns:
            QdrantClient: Qdrant 客户端实例

        Raises:
            RuntimeError: 连接或初始化失败时抛出
        """
        if self._client is not None:
            logger.debug("Qdrant 已连接，跳过重复 connect")
            return self._client

        try:
            logger.info(f"正在连接到 Qdrant: {config.qdrant_url}")

            self._client = QdrantClient(
                url=config.qdrant_url,
                api_key=config.qdrant_api_key or "",
                timeout=30,
            )

            # 检查健康状态
            health = self._client.get_collections()
            logger.info(f"成功连接到 Qdrant，已有 {len(health.collections)} 个集合")

            # 检查并创建 collection
            if not self._collection_exists():
                logger.info(f"collection '{self.COLLECTION_NAME}' 不存在，正在创建...")
                self._create_collection()
                logger.info(f"成功创建 collection '{self.COLLECTION_NAME}'")
            else:
                logger.info(f"collection '{self.COLLECTION_NAME}' 已存在")
                # 检查向量维度是否匹配
                collection_info = self._client.get_collection(self.COLLECTION_NAME)
                existing_dim = collection_info.config.params.vectors.size
                if existing_dim != self.VECTOR_DIM:
                    logger.warning(
                        f"检测到向量维度不匹配！当前: {existing_dim}, 配置: {self.VECTOR_DIM}，重建 collection..."
                    )
                    self._client.delete_collection(self.COLLECTION_NAME)
                    self._create_collection()
                    logger.info(f"成功重建 collection，维度: {self.VECTOR_DIM}")

            return self._client

        except UnexpectedResponse as e:
            logger.error(f"Qdrant 连接失败: {e}")
            self.close()
            raise RuntimeError(f"Qdrant 连接失败: {e}") from e
        except Exception as e:
            logger.error(f"Qdrant 连接失败: {e}")
            self.close()
            raise RuntimeError(f"Qdrant 连接失败: {e}") from e

    def _collection_exists(self) -> bool:
        """检查 collection 是否存在"""
        collections = self._client.get_collections().collections
        return any(c.name == self.COLLECTION_NAME for c in collections)

    def _create_collection(self) -> None:
        """创建 biz collection"""
        self._client.create_collection(
            collection_name=self.COLLECTION_NAME,
            vectors_config=VectorParams(
                size=self.VECTOR_DIM,
                distance=Distance.COSINE,
            ),
        )

    def get_client(self) -> QdrantClient:
        """
        获取 Qdrant 客户端实例

        Returns:
            QdrantClient: 客户端实例

        Raises:
            RuntimeError: 客户端未初始化时抛出
        """
        if self._client is None:
            raise RuntimeError("Qdrant 客户端未初始化，请先调用 connect()")
        return self._client

    def health_check(self) -> bool:
        """
        健康检查

        Returns:
            bool: True 表示健康
        """
        try:
            if self._client is None:
                return False
            self._client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant 健康检查失败: {e}")
            return False

    def close(self) -> None:
        """关闭连接"""
        if self._client is not None:
            self._client.close()
            self._client = None
            logger.info("已关闭 Qdrant 连接")

    def __enter__(self) -> "QdrantClientManager":
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: object
    ) -> None:
        """上下文管理器退出"""
        self.close()


# 全局单例
qdrant_manager = QdrantClientManager()
