from typing import Iterator, List, Dict

from .llm_adapters import create_adapter, BaseLLMAdapter


class AgentsLLM:
    """
    Agents 统一 LLM 客户端
    """

    def __init__(
            self,
            model: str,
            api_key: str,
            base_url: str
    ):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url

        self._adapter: BaseLLMAdapter = create_adapter(
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model
        )

    def invoke(self, messages: List[Dict[str, str]]) -> str:
        """
        非流式调用 LLM，返回完整响应对象
        """
        return self._adapter.invoke(messages)

    def stream_invoke(self, message: List[Dict[str, str]]) -> Iterator[str]:
        """
        流式调用 LLM
        """
        for chunk in self._adapter.stream_invoke(message):
            yield chunk
