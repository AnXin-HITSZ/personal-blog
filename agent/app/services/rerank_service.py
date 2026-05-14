"""重排服务 — 基于 Cross-Encoder 的检索后重排

使用 BGE Reranker 系列模型（通过 sentence-transformers CrossEncoder 加载），
对第一阶段召回的结果进行精细化打分排序，提升最终检索质量。

架构定位:
  召回阶段 (Qdrant 向量检索) → 重排阶段 (Cross-Encoder) → Top-K 结果 → LLM
  第一轮 fast but coarse        第二轮 slow but fine
"""

from typing import List, Tuple

from langchain_core.documents import Document
from loguru import logger

from app.config import config


class RerankService:
    """重排服务 — 对已召回的文档进行 Cross-Encoder 重排"""

    def __init__(self):
        self._model = None
        self._initialized = False

    def _lazy_init(self):
        """延迟加载重排模型（首次调用时加载，避免启动阻塞）"""
        if self._initialized:
            return

        try:
            from sentence_transformers import CrossEncoder

            model_path = config.rag_rerank_model_path

            logger.info(
                f"正在加载重排模型: {model_path}, "
                f"device={config.rag_rerank_device}"
            )

            self._model = CrossEncoder(
                model_path,
                device=config.rag_rerank_device,
            )

            self._initialized = True
            logger.info("重排模型加载完成")

        except Exception as e:
            logger.error(f"重排模型加载失败: {e}")
            raise

    def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: int = 3,
    ) -> List[Tuple[Document, float]]:
        """对召回的文档进行重排，返回得分最高的 top_k 个

        Args:
            query: 用户查询
            documents: 第一阶段召回结果
            top_k: 最终保留数量

        Returns:
            List[Tuple[Document, float]]: 排序后的 (文档, 分数) 列表，分数越高越相关
        """
        if not documents:
            return []

        try:
            self._lazy_init()

            # 构建 query-doc 对
            pairs = [(query, doc.page_content) for doc in documents]
            scores = self._model.predict(pairs)

            logger.debug(
                f"重排完成: {len(documents)} 个候选文档, "
                f"得分范围: {float(min(scores)):.4f} ~ {float(max(scores)):.4f}"
            )

            # 按分数从高到低排序
            scored = list(zip(documents, scores.tolist()))
            scored.sort(key=lambda x: x[1], reverse=True)

            return scored[:top_k]

        except Exception as e:
            logger.error(f"重排过程失败: {e}")
            # 降级：返回原始顺序的前 top_k 个
            return [(doc, 0.0) for doc in documents[:top_k]]


# 全局单例
rerank_service = RerankService()
