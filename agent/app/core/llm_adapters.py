import time
from abc import ABC, abstractmethod
from typing import Optional, Iterator, List, Dict, Any, Union, AsyncIterator

from .exceptions import AgentException
from .llm_response import LLMResponse, StreamStats

class BaseLLMAdapter(ABC):
    """
    LLM 适配器基类
    """

    def __init__(self, api_key: str, base_url: Optional[str], timeout: int, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.model = model
        self._client = None
        self._async_client = None

    @abstractmethod
    def create_client(self) -> Any:
        """
        创建客户端实例
        """
        pass

    @abstractmethod
    def stream_invoke(self, messages: List[Dict], **kwargs) -> Iterator[str]:
        """
        流式调用，返回生成器
        """
        pass

    def _is_thinking_model(self, model_name: str) -> bool:
        """
        判断是否为 thinking model
        """
        thinking_keywords = ["reasoner", "o1", "o3", "thinking"]
        model_lower = model_name.lower()
        return any(keyword in model_lower for keyword in thinking_keywords)

class OpenAIAdapter(BaseLLMAdapter):
    """
    OpenAI 兼容接口适配器（默认）
    """

    def create_client(self) -> Any:
        """
        创建 OpenAI 客户端
        """
        from openai import OpenAI

        return OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )

    def stream_invoke(self, messages: List[Dict], **kwargs) -> Iterator[str]:
        """
        流式调用
        """
        if not self._client:
            self._client = self.create_client()

        start_time = time.time()

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                **kwargs
            )

            collected_content = []
            reasoning_content = None
            usage = {}

            for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta

                    if delta.content:
                        collected_content.append(delta.content)
                        yield delta.content

                    if self._is_thinking_model(self.model):
                        if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                            reasoning_content = ""
                        reasoning_content += delta.reasoning_content

                if hasattr(chunk, 'usage') and chunk.usage:
                    usage = {
                        "prompt_tokens": chunk.usage.prompt_tokens,
                        "completion_tokens": chunk.usage.completion_tokens,
                        "total_tokens": chunk.usage.total_tokens,
                    }

            latency_ms = int((time.time() - start_time) * 1000)

            self.last_stats = StreamStats(
                model=self.model,
                usage=usage,
                latency_ms=latency_ms,
                reasoning_content=reasoning_content
            )

        except Exception as e:
            raise AgentException(f"OpenAI API 流式调用失败: {str(e)}")

def create_adapter(
        api_key: str,
        base_url: Optional[str],
        timeout: int,
        model: str
) -> BaseLLMAdapter:
    """
    根据 base_url 自动选择适配器
    """
    if base_url:
        base_url_lower = base_url.lower()

        if "anthropic.com" in base_url_lower:
            # TODO: return AnthropicAdapter
            pass

        if "googleapis.com" in base_url_lower or "generativelanguage" in base_url_lower:
            # TODO: return GeminiAdapter
            pass

    return OpenAIAdapter(api_key, base_url, timeout, model)
