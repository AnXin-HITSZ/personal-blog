from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Union, Any
from collections.abc import Iterator

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
    def _get_enhanced_system_prompt(self) -> str:
        """
        构建增强的系统提示词，包含工具信息
        """
        pass

    @abstractmethod
    def run(
            self,
            input_text: str,
            stream: bool = True
    ) -> Union[str, Iterator[Dict[str, Any]]]:
        """
        运行 Agent
        """
        pass

    def _build_messages(self, enhanced_system_prompt: str, input_text: str) -> List[Dict[str, str]]:
        """
        构建消息列表
        """
        messages = []

        messages.append({
            "role": "system",
            "content": enhanced_system_prompt
        })

        for msg in self._history:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

        messages.append({
            "role": "user",
            "content": input_text
        })

        return messages

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
