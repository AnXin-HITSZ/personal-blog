"""RAG 搜索与管理接口模块"""

from pathlib import Path

from fastapi import APIRouter, Body, HTTPException, Query
from fastapi.responses import JSONResponse
from loguru import logger

from app.services.vector_store_manager import vector_store_manager

router = APIRouter()


@router.post("/rag/search")
async def rag_search(
    query: str = Body(..., description="搜索关键词"),
    top_k: int = Body(3, description="返回结果数量", ge=1, le=20),
):
    """
    语义搜索知识库

    Args:
        query: 搜索关键词
        top_k: 返回结果数量 (1-20)

    Returns:
        JSONResponse: 搜索结果
    """
    try:
        logger.info(f"RAG 搜索: query='{query}', top_k={top_k}")

        vector_store = vector_store_manager.get_vector_store()
        docs_with_scores = vector_store.similarity_search_with_relevance_scores(
            query, k=top_k
        )

        results = []
        for doc, score in docs_with_scores:
            results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": round(score, 4),
            })

        logger.info(f"RAG 搜索完成: 找到 {len(results)} 个结果")

        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "message": "success",
                "data": {
                    "query": query,
                    "total": len(results),
                    "results": results,
                },
            },
        )

    except Exception as e:
        logger.error(f"RAG 搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {e}")


@router.delete("/rag/source")
async def delete_source(file_path: str = Query(..., description="要删除的文件路径")):
    """
    删除指定文件的所有向量索引及源文件

    Args:
        file_path: 文件路径

    Returns:
        JSONResponse: 删除结果
    """
    try:
        logger.info(f"删除索引: file_path='{file_path}'")

        # 1. 删除 Qdrant 向量索引
        deleted_count = vector_store_manager.delete_by_source(file_path)

        # 2. 删除磁盘上的源文件
        file_on_disk = Path(file_path)
        file_removed = False
        if file_on_disk.exists():
            file_on_disk.unlink()
            file_removed = True
            logger.info(f"已删除源文件: {file_path}")

        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "message": "success",
                "data": {
                    "file_path": file_path,
                    "deleted_count": deleted_count,
                    "file_removed": file_removed,
                },
            },
        )

    except Exception as e:
        logger.error(f"删除索引失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除索引失败: {e}")


@router.get("/rag/stats")
async def rag_stats():
    """
    获取知识库统计信息

    Returns:
        JSONResponse: 统计信息
    """
    try:
        from app.core.qdrant_client import qdrant_manager

        client = qdrant_manager.get_client()
        collection_info = client.get_collection(qdrant_manager.COLLECTION_NAME)
        entity_count = collection_info.points_count
        vector_dim = collection_info.config.params.vectors.size

        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "message": "success",
                "data": {
                    "collection": qdrant_manager.COLLECTION_NAME,
                    "total_entities": entity_count,
                    "vector_dim": vector_dim,
                },
            },
        )

    except Exception as e:
        logger.error(f"获取知识库统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {e}")
