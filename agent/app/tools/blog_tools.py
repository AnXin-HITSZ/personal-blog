"""博客工具 - 自动编写并发布博客文章

提供 `publish_article` 工具，Agent 通过内部 API Key 认证，
调用后端 `POST /api/article/add` 接口完成文章发布。
"""

import os
import httpx
from langchain_core.tools import tool
from loguru import logger

BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8080")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")


@tool
def publish_article(title: str, content: str, user_id: int = 1) -> str:
    """发布一篇新的博客文章

    调用后端接口创建博客文章。内容为 Markdown 格式，支持完整的 Markdown 语法。
    调用此工具前应确保内容已由 LLM 生成完整。

    Args:
        title: 文章标题
        content: 文章内容（完整的 Markdown 文本）
        user_id: 作者用户 ID（默认 1，即管理员）

    Returns:
        发布结果描述，包含文章 ID 或错误信息
    """
    url = f"{BACKEND_BASE_URL}/api/article/add"
    headers = {"Content-Type": "application/json"}
    if INTERNAL_API_KEY:
        headers["X-Internal-Api-Key"] = INTERNAL_API_KEY

    payload = {
        "title": title,
        "content": content,
        "userId": user_id,
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload, headers=headers)
            data = resp.json()

        if resp.status_code == 200 and data.get("success"):
            article = data.get("data", {})
            article_id = article.get("articleId", "未知")
            return (
                f"✅ 文章发布成功！\n"
                f"   标题: {title}\n"
                f"   文章 ID: {article_id}\n"
                f"   你可以通过前端页面查看文章。"
            )
        else:
            error_msg = data.get("errorMsg", f"HTTP {resp.status_code}")
            return f"❌ 文章发布失败: {error_msg}"

    except httpx.ConnectError:
        logger.error(f"无法连接到后端服务: {url}")
        return f"❌ 发布失败: 无法连接到后端服务 {BACKEND_BASE_URL}，请确认后端已启动。"
    except Exception as e:
        logger.error(f"publish_article 异常: {e}")
        return f"❌ 发布失败: {e}"
