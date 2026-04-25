from abc import ABC, abstractmethod
from typing import Any


class BaseMemory(ABC):
    """
    记忆基类
    """

    @abstractmethod
    def add(self, user_id: str, content: Any):
        """
        添加记忆
        """
        pass

    @abstractmethod
    def retrieve(self, user_id: str, query: Any):
        """
        检索记忆
        """
        pass

    @abstractmethod
    def clear(self, user_id: str):
        """
        清除用户记忆
        """
        pass
