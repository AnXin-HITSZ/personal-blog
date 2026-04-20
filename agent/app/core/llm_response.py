from typing import Optional, Dict, List
from dataclasses import dataclass, field

@dataclass
class LLMResponse:
    """
    统一的 LLM 响应对象
    """

    """ 回复内容 """
    content: str

    """ 实际使用的模型名称 """
    model: str

    """ Token 使用统计 """
    usage: Dict[str, str] = field(default_factory=dict)

    """ 调用耗时（毫秒） """
    latency_ms: int = 0

    """ 推理过程 """
    reasoning_content: Optional[str] = None

    def __str__(self) -> str:
        """
        直接打印返回 content
        """
        return self.content

    def __repr__(self) -> str:
        """
        详细信息展示
        """
        parts = [
            f"LLMResponse(model={self.model})",
            f"latency={self.latency_ms}ms",
            f"tokens={self.usage.get('total_tokens', 0)}",
        ]
        if self.reasoning_content:
            parts.append("has_reasoning=True")
        parts.append(f"content_length={len(self.content)}")
        return ", ".join(parts)

    def to_dict(self) -> Dict:
        """
        转换为字典格式，方便日志记录
        """
        result = {
            "content": self.content,
            "model": self.model,
            "usage": self.usage,
            "latency_ms": self.latency_ms,
        }
        if self.reasoning_content:
            result["reasoning_content"] = self.reasoning_content
        return result

@dataclass
class StreamStats:
    """
    流式调用的统计信息
    """

    """ 实际使用的模型名称 """
    model: str

    """ Token 使用统计 """
    usage: Dict[str, int] = field(default_factory=dict)

    """ 调用耗时（毫秒） """
    latency_ms: int = 0

    """ 推理过程（仅 thinking model） """
    reasoning_content: Optional[str] = None

    def to_dict(self) -> Dict:
        """
        转换为字典格式
        """
        result = {
            "model": self.model,
            "usage": self.usage,
            "latency_ms": self.latency_ms,
        }
        if self.reasoning_content:
            result["reasoning_content"] = self.reasoning_content
        return result
