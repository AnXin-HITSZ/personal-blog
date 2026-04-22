from typing import List, Dict
import json

from .client import redis_client
from .config import REDIS_CHAT_HISTORY_KEY_PREFIX, CHAT_SESSION_EXPIRE

class RedisChatService:
    """
    AI 对话历史 Redis 服务
    """

    @staticmethod
    def get_chat_history(session_id: str) -> List[Dict]:
        """
        获取用户对话历史
        """
        key = f"{REDIS_CHAT_HISTORY_KEY_PREFIX}{session_id}"
        data = redis_client.get(key)
        return json.loads(data) if data else []

    @staticmethod
    def save_chat_history(session_id: str, history: List[Dict]) -> None:
        """
        保存 / 更新用户对话历史（自动过期）
        """
        key = f"{REDIS_CHAT_HISTORY_KEY_PREFIX}{session_id}"
        redis_client.setex(
            name=key,
            time=CHAT_SESSION_EXPIRE,
            value=json.dumps(history, ensure_ascii=False)
        )

    @staticmethod
    def delete_chat_history(session_id: str) -> None:
        """
        删除对话历史
        """
        key = f"{REDIS_CHAT_HISTORY_KEY_PREFIX}{session_id}"
        redis_client.delete(key)
