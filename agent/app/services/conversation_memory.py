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
