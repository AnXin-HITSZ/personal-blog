import json
import urllib.request
import os
from typing import Dict, Any, List

from app.tools.base import Tool, ToolParameter


BACKEND_BASE_URL = os.getenv('BACKEND_BASE_URL', 'http://localhost:8080')


class WriteBlogTool(Tool):
    """
    撰写博客文章工具：调用 SpringBoot 后端新增文章接口
    """

    def __init__(self):
        super().__init__(
            name="write_blog",
            description="根据用户意图撰写一篇博客文章，调用后端接口创建文章并持久化到数据库"
        )

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="title",
                type="string",
                description="博客文章标题",
                required=True,
            ),
            ToolParameter(
                name="content",
                type="string",
                description="博客文章正文内容（支持 Markdown 格式）",
                required=True,
            ),
            ToolParameter(
                name="userId",
                type="integer",
                description="文章作者的用户 ID，必须填写当前登录用户的 ID",
                required=True,
            ),
        ]

    def run(self, parameters: Dict[str, Any]) -> str:
        title = (parameters.get("title") or "").strip()
        content = (parameters.get("content") or "").strip()
        user_id = parameters.get("userId")

        if not title:
            return "错误：文章标题不能为空"
        if not content:
            return "错误：文章内容不能为空"
        if not user_id:
            return "错误：缺少作者用户 ID"

        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            return f"错误：无效的用户 ID: {user_id}"

        body = json.dumps({
            "userId": user_id,
            "title": title,
            "content": content,
        }, ensure_ascii=False).encode("utf-8")

        url = f"{BACKEND_BASE_URL}/api/article/add"
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                resp_body = resp.read().decode("utf-8")
                result = json.loads(resp_body)

            if result.get("success"):
                article = result.get("data", {})
                article_id = article.get("articleId") if article else "未知"
                return (
                    f"✅ 博客文章发布成功！\n"
                    f"- 文章 ID: {article_id}\n"
                    f"- 标题: {title}\n"
                    f"- 作者 ID: {user_id}\n\n"
                    f"文章已持久化到数据库，用户可在博客首页查看。"
                )
            else:
                return f"❌ 文章发布失败: {result.get('errorMsg', '未知错误')}"

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            return f"❌ 后端接口错误 (HTTP {e.code}): {error_body}"
        except urllib.error.URLError as e:
            return f"❌ 无法连接后端服务: {e.reason}"
        except Exception as e:
            return f"❌ 文章发布异常: {str(e)}"
