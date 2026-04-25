from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List


class BaseLLMAdapter(ABC):
    """
    LLM 适配器基类
    """

    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self._client = None

    @abstractmethod
    def create_client(self) -> Any:
        """
        创建客户端实例
        """
        pass

    @abstractmethod
    def invoke(self, message: List[Dict]) -> str:
        """
        非流式调用
        """
        pass

    @abstractmethod
    def stream_invoke(self, message: List[Dict]) -> Iterator[str]:
        """
        流式调用，返回生成器
        """
        pass

class OpenAIAdapter(BaseLLMAdapter):
    """
    OpenAI 兼容接口适配器
    """

    def create_client(self) -> Any:
        """
        创建 OpenAI 客户端
        """
        from openai import OpenAI

        return OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def invoke(self, message: List[Dict]) -> str:
        """
        非流式调用
        """
        if not self._client:
            self._client = self.create_client()

        response = self._client.chat.completions.create(
            model=self.model,
            messages=message
        )

        choice = response.choices[0]
        content = choice.message.content or ""

        return content

    def stream_invoke(self, messages: List[Dict]) -> Iterator[str]:
        """
        流式调用
        """
        if not self._client:
            self._client = self.create_client()

        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True
        )

        collected_content = []

        for chunk in response:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta

                if delta.content:
                    collected_content.append(delta.content)
                    yield delta.content

def create_adapter(
        api_key: str,
        base_url: str,
        model: str
) -> BaseLLMAdapter:
    """
    创建适配器
    """
    return OpenAIAdapter(api_key, base_url, model)
