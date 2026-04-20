import os
from typing import Optional, Iterator, List, Dict, Union, Any, AsyncIterator

from .exceptions import AgentsException
from .llm_adapters import BaseLLMAdapter, create_adapter
from .llm_response import StreamStats

class AgentsLLM:
    """
    Agents 统一 LLM 客户端
    """

    def __init__(
            self,
            model: Optional[str] = None,
            api_key: Optional[str] = None,
            base_url: Optional[str] = None,
            temperature: float = 0.7,
            max_tokens: Optional[int] = None,
            timeout: Optional[int] = None,
            **kwargs
    ):
        """
        初始化 LLM 客户端
        """
        self.model = model or os.getenv("LLM_MODEL_ID")
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.base_url = base_url or os.getenv("LLM_BASE_URL")
        self.timeout = timeout or int(os.getenv("LLM_TIMEOUT", "60"))

        self.temperature = temperature
        self.max_tokens = max_tokens
        self.kwargs = kwargs

        if not self.model:
            raise AgentsException("必须提供模型名称（model 参数或 LLM_MODEL_ID 环境变量）")
        if not self.api_key:
            raise AgentsException("必须提供 API 密钥（api_key 参数或 LLM_API_KEY 环境变量）")
        if not self.base_url:
            raise AgentsException("必须提供服务地址（base_url 参数或 LLM_BASE_URL 环境变量）")

        self._adapter: BaseLLMAdapter = create_adapter(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
            model=self.model
        )

        self.last_call_stats: Optional[StreamStats] = None

    def think(self, messages: List[Dict[str, str]], temperature: Optional[float] = None) -> Iterator[str]:
        """
        调用大语言模型进行思考，并返回流式响应
        """
        print(f"正在调用 {self.model} 模型 ...")

        kwargs = {
            "temperature": temperature if temperature is not None else self.temperature,
        }
        if self.max_tokens:
            kwargs["max_tokens"] = self.max_tokens

        try:
            print("大语言模型响应成功: ")
            for chunk in self._adapter.stream_invoke(messages, **kwargs):
                print(chunk, end="", flush=True)
                yield chunk
            print()

            if hasattr(self._adapter, 'last_stats'):
                self.last_call_stats = self._adapter.last_stats

        except Exception as e:
            print(f"调用 LLM API 时发生错误: {e}")
            raise

    def stream_invoke(self, messages: List[Dict[str, str]], **kwargs) -> Iterator[str]:
        """
        流式调用 LLM 的别名方法，与 think 方法功能相同
        """
        temperature = kwargs.pop("temperature", None)

        call_kwargs = {}
        if self.max_tokens:
            call_kwargs["max_tokens"] = kwargs.pop("max_tokens", self.max_tokens)
        call_kwargs.update(kwargs)

        for chunk in self._adapter.stream_invoke(messages, temperature=temperature, **call_kwargs):
            yield chunk

        if hasattr(self._adapter, 'last_stats'):
            self.last_call_stats = self._adapter.last_stats
