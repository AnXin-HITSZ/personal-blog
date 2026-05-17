"""数据库工具 - 从 MySQL 查询文章和用户数据

提供只读查询工具，补充向量检索（RAG）无法覆盖的精确查询场景。
直接从数据库获取实时的文章统计、用户数据等。
"""

import os
from typing import Optional

import pymysql
from pymysql.cursors import DictCursor
from langchain_core.tools import tool
from loguru import logger

# ─── 数据库连接配置 ───
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root123456")
DB_NAME = os.getenv("DB_NAME", "personal_blog")


def _get_conn():
    """创建数据库连接"""
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        cursorclass=DictCursor,
    )


@tool
def get_article_stats() -> str:
    """获取文章统计信息：总数、本月新增、近6个月发布趋势"""
    conn = None
    try:
        conn = _get_conn()
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total FROM tb_article")
            total = cursor.fetchone()["total"]

            cursor.execute(
                "SELECT COUNT(*) AS cnt FROM tb_article "
                "WHERE DATE_FORMAT(create_time, '%Y-%m') = DATE_FORMAT(NOW(), '%Y-%m')"
            )
            monthly = cursor.fetchone()["cnt"]

            cursor.execute(
                "SELECT DATE_FORMAT(create_time, '%Y-%m') AS month, COUNT(*) AS cnt "
                "FROM tb_article "
                "WHERE create_time >= DATE_SUB(NOW(), INTERVAL 6 MONTH) "
                "GROUP BY month ORDER BY month DESC"
            )
            trend = cursor.fetchall()

        lines = [
            f"📊 文章统计",
            f"总文章数: {total}",
            f"本月新增: {monthly}",
        ]
        if trend:
            lines.append("")
            lines.append("近 6 个月发布趋势:")
            for row in trend:
                lines.append(f"  {row['month']}: {row['cnt']} 篇")
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"get_article_stats 失败: {e}")
        return f"查询文章统计失败: {e}"
    finally:
        if conn:
            conn.close()


@tool
def search_articles_db(keyword: str, limit: int = 10) -> str:
    """在文章标题和内容中搜索关键词（直接从 MySQL 精确匹配）

    Args:
        keyword: 搜索关键词
        limit: 最多返回多少条结果（默认 10）
    """
    conn = None
    try:
        conn = _get_conn()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT article_id, title, create_time FROM tb_article "
                "WHERE title LIKE %s OR content LIKE %s "
                "ORDER BY create_time DESC LIMIT %s",
                (f"%{keyword}%", f"%{keyword}%", limit),
            )
            rows = cursor.fetchall()

        if not rows:
            return f"未找到包含「{keyword}」的文章"

        lines = [f"找到 {len(rows)} 篇包含「{keyword}」的文章:", ""]
        for row in rows:
            ts = row["create_time"].strftime("%Y-%m-%d %H:%M")
            lines.append(f"  #{row['article_id']} {row['title']}")
            lines.append(f"      {ts}")
            lines.append("")
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"search_articles_db 失败: {e}")
        return f"搜索文章失败: {e}"
    finally:
        if conn:
            conn.close()


@tool
def get_recent_articles_db(limit: int = 5) -> str:
    """获取最近发布的文章列表（直接从 MySQL 查询）

    Args:
        limit: 返回多少篇（默认 5）
    """
    conn = None
    try:
        conn = _get_conn()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT article_id, title, create_time, update_time "
                "FROM tb_article ORDER BY create_time DESC LIMIT %s",
                (limit,),
            )
            rows = cursor.fetchall()

        if not rows:
            return "暂无文章"

        lines = [f"📝 最近 {len(rows)} 篇文章:", ""]
        for row in rows:
            lines.append(
                f"  #{row['article_id']} {row['title']}\n"
                f"    创建: {row['create_time'].strftime('%Y-%m-%d %H:%M')}\n"
                f"    更新: {row['update_time'].strftime('%Y-%m-%d %H:%M')}\n"
            )
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"get_recent_articles_db 失败: {e}")
        return f"查询文章列表失败: {e}"
    finally:
        if conn:
            conn.close()


@tool
def get_article_detail(article_id: int) -> str:
    """根据 ID 获取文章详情（含作者名、内容预览）

    Args:
        article_id: 文章 ID
    """
    conn = None
    try:
        conn = _get_conn()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT a.*, u.username FROM tb_article a "
                "LEFT JOIN tb_user u ON a.user_id = u.user_id "
                "WHERE a.article_id = %s",
                (article_id,),
            )
            row = cursor.fetchone()

        if not row:
            return f"未找到 ID 为 {article_id} 的文章"

        preview = (
            row["content"][:300] + "..."
            if len(row["content"]) > 300
            else row["content"]
        )

        return (
            f"📄 文章详情\n"
            f"标题: {row['title']}\n"
            f"作者: {row['username']}\n"
            f"创建: {row['create_time'].strftime('%Y-%m-%d %H:%M')}\n"
            f"更新: {row['update_time'].strftime('%Y-%m-%d %H:%M')}\n\n"
            f"内容预览:\n{preview}"
        )
    except Exception as e:
        logger.error(f"get_article_detail 失败: {e}")
        return f"查询文章详情失败: {e}"
    finally:
        if conn:
            conn.close()


@tool
def get_user_stats() -> str:
    """获取用户统计信息：总数、管理员/普通用户分布、近6个月注册趋势"""
    conn = None
    try:
        conn = _get_conn()
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total FROM tb_user")
            total = cursor.fetchone()["total"]

            cursor.execute(
                "SELECT is_admin, COUNT(*) AS cnt FROM tb_user GROUP BY is_admin"
            )
            roles = cursor.fetchall()

            cursor.execute(
                "SELECT DATE_FORMAT(create_time, '%Y-%m') AS month, COUNT(*) AS cnt "
                "FROM tb_user "
                "WHERE create_time >= DATE_SUB(NOW(), INTERVAL 6 MONTH) "
                "GROUP BY month ORDER BY month DESC"
            )
            trend = cursor.fetchall()

        lines = ["👥 用户统计", f"总用户数: {total}", ""]
        for row in roles:
            label = "管理员" if row["is_admin"] == 1 else "普通用户"
            lines.append(f"  {label}: {row['cnt']} 人")

        if trend:
            lines.append("")
            lines.append("近 6 个月注册趋势:")
            for row in trend:
                lines.append(f"  {row['month']}: {row['cnt']} 人")

        return "\n".join(lines)
    except Exception as e:
        logger.error(f"get_user_stats 失败: {e}")
        return f"查询用户统计失败: {e}"
    finally:
        if conn:
            conn.close()


@tool
def execute_read_query(sql: str) -> str:
    """执行自定义只读 SQL 查询（仅 SELECT 语句）

    用于上述专用工具无法覆盖的查询场景。
    仅允许 SELECT，拒绝 INSERT/UPDATE/DELETE/DROP/ALTER 等操作。

    Args:
        sql: SELECT 查询语句
    """
    stripped = sql.strip()
    if not stripped.upper().startswith("SELECT"):
        return "❌ 仅支持 SELECT 查询"

    conn = None
    try:
        conn = _get_conn()
        with conn.cursor() as cursor:
            cursor.execute(stripped)
            rows = cursor.fetchall()

        if not rows:
            return "查询结果为空"

        headers = list(rows[0].keys())
        col_widths = [
            max(len(h), max((len(str(r[h])) for r in rows), default=0))
            for h in headers
        ]

        header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
        sep = "-+-".join("-" * w for w in col_widths)

        lines = [header_line, sep]
        for row in rows:
            vals = [
                str(row[h])[:60] if row[h] is not None else "NULL"
                for h in headers
            ]
            lines.append(
                " | ".join(vals[i].ljust(col_widths[i]) for i in range(len(headers)))
            )

        lines.append(f"\n共 {len(rows)} 行")
        return "\n".join(lines)

    except Exception as e:
        return f"❌ 查询失败: {e}"
    finally:
        if conn:
            conn.close()
