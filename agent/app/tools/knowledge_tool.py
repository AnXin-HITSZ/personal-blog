"""知识检索工具 - 从向量数据库中检索相关信息

采用"先召回后重排"两阶段架构：
  1. 第一阶段：从 Qdrant 向量库召回 N 个候选文档（快速粗筛）
  2. 第二阶段：Cross-Encoder 对候选文档重排，保留 Top-K（精细排序）
"""

from typing import List, Tuple

from langchain_core.documents import Document
from langchain_core.tools import tool
from loguru import logger

from app.config import config
from app.services.vector_store_manager import vector_store_manager
from app.services.rerank_service import rerank_service


@tool(response_format="content_and_artifact")
def retrieve_knowledge(query: str) -> Tuple[str, List[Document]]:
    """从知识库中检索相关信息来回答问题

    使用先召回（Qdrant 向量检索）后重排（Cross-Encoder）的两阶段策略，
    优先返回与问题最相关的结果。

    当用户的问题涉及专业知识、文档内容或需要参考资料时，使用此工具。

    Args:
        query: 用户的问题或查询

    Returns:
        Tuple[str, List[Document]]: (格式化的上下文文本, 原始文档列表)
    """
    try:
        logger.info(f"知识检索工具被调用: query='{query}'")

        # ═══ 第一阶段：粗召回 ═══
        vector_store = vector_store_manager.get_vector_store()
        retriever = vector_store.as_retriever(
            search_kwargs={"k": config.rag_rerank_top_n}
        )

        candidate_docs = retriever.invoke(query)

        if not candidate_docs:
            logger.warning("未检索到相关文档")
            return "没有找到相关信息。", []

        logger.info(
            f"第一阶段召回: {len(candidate_docs)} 个候选文档 "
            f"(rerank_top_n={config.rag_rerank_top_n})"
        )

        # ═══ 第二阶段：重排 ═══
        try:
            reranked = rerank_service.rerank(
                query, candidate_docs, top_k=config.rag_final_top_k
            )
            docs = [doc for doc, _ in reranked]
            logger.info(
                f"第二阶段重排完成: {len(reranked)} 个最终结果 "
                f"(final_top_k={config.rag_final_top_k})"
            )
        except Exception as e:
            logger.warning(f"重排失败，降级使用召回结果: {e}")
            docs = candidate_docs[:config.rag_final_top_k]

        # 格式化文档为上下文
        context = format_docs(docs)

        return context, docs

    except Exception as e:
        logger.error(f"知识检索工具调用失败: {e}")
        return f"检索知识时发生错误: {str(e)}", []


def format_docs(docs: List[Document]) -> str:
    """
    格式化文档列表为上下文文本

    Args:
        docs: 文档列表

    Returns:
        str: 格式化的上下文文本
    """
    formatted_parts = []

    for i, doc in enumerate(docs, 1):
        # 提取元数据
        metadata = doc.metadata
        source = metadata.get("_file_name", "未知来源")

        # 提取标题信息 (如果有)
        headers = []
        for key in ["h1", "h2", "h3"]:
            if key in metadata and metadata[key]:
                headers.append(metadata[key])

        header_str = " > ".join(headers) if headers else ""

        # 构建格式化文本
        formatted = f"【参考资料 {i}】"
        if header_str:
            formatted += f"\n标题: {header_str}"
        formatted += f"\n来源: {source}"
        formatted += f"\n内容:\n{doc.page_content}\n"

        formatted_parts.append(formatted)

    return "\n".join(formatted_parts)
