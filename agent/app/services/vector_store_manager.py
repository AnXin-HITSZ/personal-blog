"""向量存储管理器 - 封装 Qdrant VectorStore 操作"""

from typing import List

from langchain_core.documents import Document
from langchain_qdrant import Qdrant
from loguru import logger

from app.config import config
from app.core.qdrant_client import qdrant_manager
from app.services.vector_embedding_service import vector_embedding_service

# 统一使用 biz collection
COLLECTION_NAME = "biz"


class VectorStoreManager:
    """向量存储管理器"""

    def __init__(self):
        """初始化向量存储管理器"""
        self.vector_store = None
        self.collection_name = COLLECTION_NAME
        self._initialize_vector_store()

    def _initialize_vector_store(self):
        """初始化 Qdrant VectorStore"""
        try:
            _ = qdrant_manager.connect()

            # 创建 LangChain Qdrant VectorStore
            self.vector_store = Qdrant(
                client=qdrant_manager.get_client(),
                collection_name=self.collection_name,
                embeddings=vector_embedding_service,
            )

            logger.info(
                f"VectorStore 初始化成功: {config.qdrant_url}, "
                f"collection: {self.collection_name}"
            )

        except Exception as e:
            logger.error(f"VectorStore 初始化失败: {e}")
            raise

    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        批量添加文档到向量存储

        Args:
            documents: 文档列表

        Returns:
            List[str]: 文档 ID 列表
        """
        try:
            import time
            import uuid
            start_time = time.time()

            # 生成唯一 ID
            ids = [str(uuid.uuid4()) for _ in documents]

            result_ids = self.vector_store.add_documents(documents, ids=ids)

            elapsed = time.time() - start_time
            logger.info(
                f"批量添加 {len(documents)} 个文档到 VectorStore 完成, "
                f"耗时: {elapsed:.2f}秒, 平均: {elapsed / len(documents):.2f}秒/个"
            )
            return result_ids
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            raise

    def delete_by_source(self, file_path: str) -> int:
        """
        删除指定文件的所有文档

        Args:
            file_path: 文件路径（相对路径会被 resolve 为绝对路径以匹配存储值）

        Returns:
            int: 删除的文档数量
        """
        try:
            from pathlib import Path

            client = qdrant_manager.get_client()
            from qdrant_client.http.models import Filter, FieldCondition, MatchValue

            # 索引时 _source 存的是 resolve() 后的绝对路径
            normalized = Path(file_path).resolve().as_posix()

            delete_filter = Filter(
                must=[
                    FieldCondition(
                        key="metadata._source",
                        match=MatchValue(value=normalized),
                    )
                ]
            )

            result = client.delete(
                collection_name=self.collection_name,
                points_selector=delete_filter,
            )
            # qdrant-client 1.12 返回 UpdateResult(operation_id, status)，无 count
            status = getattr(result, 'status', None)
            deleted_count = 1 if status and 'completed' in str(status).lower() else 0

            logger.info(f"删除文件旧数据: {file_path}, 删除结果: {status}")
            return deleted_count

        except Exception as e:
            logger.warning(f"删除旧数据失败 (可能是首次索引): {e}")
            return 0

    def get_vector_store(self) -> Qdrant:
        """
        获取 VectorStore 实例

        Returns:
            Qdrant: VectorStore 实例
        """
        return self.vector_store


# 全局单例
vector_store_manager = VectorStoreManager()
