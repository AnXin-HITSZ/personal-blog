import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any

@dataclass
class MemoryItem:
    """
    单条记忆的数据结构
    """
    id: str = field(default_factory=lambda: f"men_{int(time.time() * 1000000)}")
    role: str = "user"
    content: str = ""
    importance: float = 0.5
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_timestamp(self) -> datetime:
        """
        将时间戳转换为人类可读的日期时间格式
        """
        return datetime.fromtimestamp(self.timestamp)

    def to_json(self) -> str:
        """
        序列化为完整的 JSON（存入 Redis Hash）
        """
        return json.dumps({
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "importance": self.importance,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "MemoryItem":
        """
        从 Redis Hash 反序列化
        """
        data = json.loads(json_str)
        return cls(**data)
