from typing import List, Dict, Tuple
from datetime import datetime

from .working_memory import WorkingMemory, MemoryItem, MemoryConfig


class UnifiedMemoryManager:
    """
    统一记忆管理器: 整合四种记忆类型
    """

    def __init__(
            self,
            redis_url: str,
            default_memory_config: MemoryConfig
    ):
        """
        初始化记忆管理器
        """
        self.default_memory_config = default_memory_config

        self.working_memory = WorkingMemory(
            redis_url=redis_url,
            config=self.default_memory_config
        )

    def add_message(
            self,
            session_id: str,
            role: str,
            content: str,
            importance: float
    ) -> str:
        """
        添加一条对话记忆
        """
        if role == "user":
            importance = 0.8
        elif role == "assistant":
            importance = 0.7
        return self.working_memory.add_message(
            session_id=session_id,
            role=role,
            content=content,
            importance=importance
        )

    def get_history(self, session_id: str) -> List[MemoryItem]:
        """
        获取对话历史
        """
        return self.working_memory.get_all(session_id=session_id)

    def retrieve(self, session_id: str, query: str, limit: int) -> List[Tuple[int, Dict[str, str]]]:
        """
        混合检索: TF-IDF + 关键词 + 时间衰减 查找相关记忆
        """
        return self.working_memory.retrieve(session_id=session_id, query=query, limit=limit)

    def clear(self, session_id: str):
        """
        清空当前会话的所有记忆
        """
        self.working_memory.clear(session_id=session_id)
