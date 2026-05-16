"""对话记忆服务 - Redis 持久化会话历史

将对话历史存储到 Redis 中，格式：

  KEY: session:{session_id}:messages
  TYPE: LIST
  VALUE: JSON 字符串，每元素 {"role":"user"|"assistant", "content":"..."}

  KEY: session:{session_id}:metadata
  TYPE: HASH
  VALUE: {created_at, updated_at, message_count}

"""

import json
from datetime import datetime
from typing import List, Optional, Dict, Any

from loguru import logger
from redis.asyncio import Redis as AsyncRedis

from app.core.redis_client import redis_manager

# Redis key 前缀
SESSION_PREFIX = "session"


def _messages_key(session_id: str) -> str:
    return f"{SESSION_PREFIX}:{session_id}:messages"


def _metadata_key(session_id: str) -> str:
    return f"{SESSION_PREFIX}:{session_id}:metadata"


def _summary_key(session_id: str) -> str:
    """会话摘要的 Redis key"""
    return f"{SESSION_PREFIX}:{session_id}:summary"


class ConversationMemory:
    """对话记忆服务 - Redis 持久化存储"""

    def __init__(self):
        """初始化对话记忆服务"""
        self._redis: Optional[AsyncRedis] = None

    async def _get_redis(self) -> AsyncRedis:
        """获取 Redis 客户端（延迟初始化）"""
        if self._redis is None:
            try:
                self._redis = await redis_manager.connect()
            except Exception as e:
                logger.error(f"对话记忆服务无法连接 Redis: {e}")
                raise
        return self._redis

    async def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """
        获取会话消息列表

        Args:
            session_id: 会话 ID

        Returns:
            List[Dict]: 消息列表 [{"role": "user", "content": "..."}, ...]
        """
        try:
            redis = await self._get_redis()
            key = _messages_key(session_id)

            items = await redis.lrange(key, 0, -1)
            messages = []
            for item in items:
                try:
                    messages.append(json.loads(item))
                except json.JSONDecodeError:
                    logger.warning(f"解析 Redis 消息失败，跳过: {item[:50]}")
                    continue

            return messages

        except Exception as e:
            logger.error(f"获取会话历史失败: {session_id}, 错误: {e}")
            return []

    async def add_message(self, session_id: str, role: str, content: str):
        """
        追加单条消息

        Args:
            session_id: 会话 ID
            role: 角色 (user/assistant)
            content: 消息内容
        """
        try:
            redis = await self._get_redis()
            key = _messages_key(session_id)

            message = {
                "role": role,
                "content": content,
            }
            await redis.rpush(key, json.dumps(message, ensure_ascii=False))

            # 更新元数据
            meta_key = _metadata_key(session_id)
            await redis.hincrby(meta_key, "message_count", 1)
            now = datetime.now().isoformat()
            await redis.hset(meta_key, "updated_at", now)
            # 首次创建时记录 created_at
            await redis.hsetnx(meta_key, "created_at", now)

        except Exception as e:
            logger.error(f"保存消息失败: {session_id}, 错误: {e}")

    async def add_messages(self, session_id: str, messages: List[Dict[str, str]]):
        """
        批量追加消息

        Args:
            session_id: 会话 ID
            messages: 消息列表 [{"role": "...", "content": "..."}, ...]
        """
        try:
            redis = await self._get_redis()
            key = _messages_key(session_id)

            pipeline = redis.pipeline()
            for msg in messages:
                pipeline.rpush(key, json.dumps(msg, ensure_ascii=False))
            pipeline.hincrby(_metadata_key(session_id), "message_count", len(messages))
            pipeline.hset(_metadata_key(session_id), "updated_at", datetime.now().isoformat())
            await pipeline.execute()

        except Exception as e:
            logger.error(f"批量保存消息失败: {session_id}, 错误: {e}")

    async def clear_session(self, session_id: str) -> bool:
        """
        清空会话

        Args:
            session_id: 会话 ID

        Returns:
            bool: 是否成功
        """
        try:
            redis = await self._get_redis()
            await redis.delete(_messages_key(session_id))
            await redis.delete(_metadata_key(session_id))
            await redis.delete(_summary_key(session_id))
            logger.info(f"已清除会话: {session_id}")
            return True

        except Exception as e:
            logger.error(f"清空会话失败: {session_id}, 错误: {e}")
            return False

    async def get_message_count(self, session_id: str) -> int:
        """
        获取会话消息数量

        Args:
            session_id: 会话 ID

        Returns:
            int: 消息数量
        """
        try:
            redis = await self._get_redis()
            count = await redis.llen(_messages_key(session_id))
            return count or 0
        except Exception:
            return 0

    # ─── 摘要压缩相关 ───

    async def save_summary(self, session_id: str, summary_text: str) -> None:
        """
        保存/更新会话摘要

        Args:
            session_id: 会话 ID
            summary_text: 摘要文本
        """
        try:
            redis = await self._get_redis()
            await redis.set(_summary_key(session_id), summary_text)
        except Exception as e:
            logger.warning(f"保存会话摘要失败: {session_id}, 错误: {e}")

    async def get_summary(self, session_id: str) -> Optional[str]:
        """
        获取会话摘要（如果存在）

        Args:
            session_id: 会话 ID

        Returns:
            Optional[str]: 摘要文本，不存在则返回 None
        """
        try:
            redis = await self._get_redis()
            summary = await redis.get(_summary_key(session_id))
            return summary if summary else None
        except Exception as e:
            logger.warning(f"获取会话摘要失败: {session_id}, 错误: {e}")
            return None

    async def clear_summary(self, session_id: str) -> bool:
        """
        清除会话摘要

        Args:
            session_id: 会话 ID

        Returns:
            bool: 是否成功
        """
        try:
            redis = await self._get_redis()
            await redis.delete(_summary_key(session_id))
            return True
        except Exception as e:
            logger.warning(f"清除会话摘要失败: {session_id}, 错误: {e}")
            return False

    async def trim_messages(self, session_id: str, keep_count: int) -> int:
        """
        裁剪消息列表，只保留最近 N 条消息

        Args:
            session_id: 会话 ID
            keep_count: 保留的消息条数

        Returns:
            int: 裁剪后的消息数量
        """
        try:
            redis = await self._get_redis()
            key = _messages_key(session_id)

            # LTRIM 保留最后 keep_count 条
            await redis.ltrim(key, -keep_count, -1)

            new_count = await redis.llen(key)
            # 更新元数据中的 message_count
            meta_key = _metadata_key(session_id)
            await redis.hset(meta_key, "message_count", new_count)

            logger.info(f"会话 {session_id} 消息已裁剪，保留 {new_count} 条")
            return new_count
        except Exception as e:
            logger.warning(f"裁剪消息失败: {session_id}, 错误: {e}")
            return 0

    async def get_messages_range(
        self, session_id: str, start: int, end: int
    ) -> List[Dict[str, Any]]:
        """
        获取指定范围内的消息

        Args:
            session_id: 会话 ID
            start: 起始索引（0-based）
            end: 结束索引（包含，-1 表示到最后）

        Returns:
            List[Dict]: 消息列表
        """
        try:
            redis = await self._get_redis()
            key = _messages_key(session_id)

            items = await redis.lrange(key, start, end)
            messages = []
            for item in items:
                try:
                    messages.append(json.loads(item))
                except json.JSONDecodeError:
                    continue

            return messages
        except Exception as e:
            logger.warning(f"获取消息范围失败: {session_id}, 错误: {e}")
            return []

    async def _get_metadata(self, session_id: str) -> Dict[str, str]:
        """获取会话元数据"""
        try:
            redis = await self._get_redis()
            meta = await redis.hgetall(_metadata_key(session_id))
            return meta or {}
        except Exception:
            return {}

    async def get_all_sessions(self) -> List[Dict[str, Any]]:
        """
        获取所有会话摘要列表（按 updated_at 倒序）

        Returns:
            List[Dict]: [{
                "session_id": str,
                "title": str,           # 首条用户消息前 50 字
                "message_count": int,
                "created_at": str,
                "updated_at": str,
            }, ...]
        """
        try:
            session_ids = await self.get_all_session_ids()
            result = []

            for sid in session_ids:
                meta = await self._get_metadata(sid)
                messages = await self.get_messages(sid)

                # 取第一条用户消息作为标题
                title = "新会话"
                for m in messages:
                    if m.get("role") == "user":
                        title = m["content"][:50]
                        break

                result.append({
                    "session_id": sid,
                    "title": title[:50],
                    "message_count": len(messages),
                    "created_at": meta.get("created_at", ""),
                    "updated_at": meta.get("updated_at", ""),
                })

            result.sort(key=lambda s: s["updated_at"], reverse=True)
            return result

        except Exception as e:
            logger.error(f"获取会话列表失败: {e}")
            return []

    async def get_all_session_ids(self) -> List[str]:
        """
        获取所有会话 ID 列表

        Returns:
            List[str]: 会话 ID 列表
        """
        try:
            redis = await self._get_redis()
            pattern = f"{SESSION_PREFIX}:*:messages"
            cursor = 0
            keys = []
            while True:
                cursor, batch = await redis.scan(cursor=cursor, match=pattern, count=100)
                keys.extend(batch)
                if cursor == 0:
                    break

            # 从 key 中提取 session_id
            prefix = f"{SESSION_PREFIX}:"
            suffix = ":messages"
            session_ids = []
            for key in keys:
                key = key if isinstance(key, str) else key.decode()
                if key.startswith(prefix) and key.endswith(suffix):
                    sid = key[len(prefix):-len(suffix)]
                    session_ids.append(sid)

            return session_ids

        except Exception as e:
            logger.error(f"获取会话列表失败: {e}")
            return []


# 全局单例
conversation_memory = ConversationMemory()
