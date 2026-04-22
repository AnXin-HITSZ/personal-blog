from abc import ABC, abstractmethod
from typing import Optional, Any
from .message import Message
from .llm import AgentsLLM
from ..tools.registry import ToolRegistry


class Agent(ABC):
    """
    Agent 基类
    """

    def __init__(
            self,
            name: str,
            llm: AgentsLLM,
            tool_registry: Optional['ToolRegistry'] = None
    ):
        self.name = name
        self.llm = llm
        self.tool_registry = tool_registry
        self._history: list[Message] = []

    @abstractmethod
    def run(self, input_text: str, max_tool_iterations: int, **kwargs) -> str:
        """
        运行 Agent
        """
        pass

    def add_message(self, message: Message):
        """
        添加消息到历史记录
        """
        self._history.append(message)

    def clear_history(self):
        """
        清空历史记录
        """
        self._history.clear()

    def get_history(self) -> list[Message]:
        """
        获取历史记录
        """
        return self._history.copy()

    def __str__(self) -> str:
        return f"Agent(name={self.name})"
