from collections.abc import Iterator
from typing import Optional, Dict, List, Any, Union
import re

from app.core.agent import Agent
from app.core.llm import AgentsLLM
from app.tools.registry import ToolRegistry
from app.core.message import Message


class SimpleAgent(Agent):
    """
    简单的对话 Agent，支持工具调用
    """

    def __init__(
            self,
            name: str,
            llm: AgentsLLM,
            tool_registry: Optional['ToolRegistry'] = None
    ):
        """
        初始化 SimpleAgent
        """
        super().__init__(
            name,
            llm,
            tool_registry
        )

    def run(
            self,
            input_text: str,
            max_tool_iterations: int = 3,
            stream=True,
            **kwargs
    ) -> Union[str, Iterator[str]]:
        """
        运行 SimpleAgent
        """
        messages = self._build_messages(input_text)

        final_messages = self._execute_tool_loop(messages, max_tool_iterations, **kwargs)

        if stream:
            return self._stream_final_response(input_text, final_messages, **kwargs)
        else:
            return self._non_stream_final_response(input_text, final_messages, **kwargs)

    def _build_messages(self, input_text: str) -> List[Dict[str, str]]:
        """
        构建消息列表
        """
        messages = []

        enhanced_prompt = self._get_enhanced_system_prompt()
        messages.append({
            "role": "system",
            "content": enhanced_prompt
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

    def _get_enhanced_system_prompt(self) -> str:
        """
        构建增强的系统提示词，包含工具信息
        """
        base_prompt = ""

        tools_description = self.tool_registry.get_tools_description()
        if not tools_description or tools_description == "暂无可用工具":
            return base_prompt

        tools_section = "\n\n## 可用工具\n"
        tools_section += "你可以使用以下工具来帮助回答问题:\n"
        tools_section += tools_description + "\n"

        tools_section += "\n## 工具调用格式\n"
        tools_section += "当需要使用工具时，请使用以下格式:\n"
        tools_section += "`[TOOL_CALL:{tool_name}:{parameters}]`\n"
        tools_section += "要求:\n"
        tools_section += "1. {tool_name} 替换为工具名称\n"
        tools_section += "2. {parameters} 替换为 JSON 格式的参数字符串\n"
        tools_section += "3. 如果工具不需要参数，parameters 部分留空即可，例如: `[TOOL_CALL:get_current_time:]`\n"
        tools_section += "4. 如果只有一个简单参数，也可以直接填值，例如: `[TOOL_CALL:search:Python]`\n\n"
        tools_section += "工具调用结果会自动插入到对话中，然后你可以基于结果继续回答。\n"

        return base_prompt + tools_section

    def _execute_tool_loop(
            self,
            messages: List[Dict[str, Any]],
            max_tool_iterations: int,
            **kwargs
    ) -> list:
        """
        运行工具调用，返回最终的 messages 列表
        """
        current_iteration = 0

        while current_iteration < max_tool_iterations:
            response = self.llm.invoke(messages, **kwargs)

            tool_calls = self.tool_registry.parse_tool_calls(response)

            if tool_calls:
                print(f"检测到 {len(tool_calls)} 个工具调用")
                tool_results = []
                clean_response = response

                for call in tool_calls:
                    result = self.tool_registry.execute_tool(call['tool_name'], call['parameters'])
                    tool_results.append(result)
                    clean_response = clean_response.replace(call['original'], '', -1)

                messages.append({
                    "role": "assistant",
                    "content": clean_response
                })

                tool_results_text = "\n\n".join(tool_results)
                messages.append({
                    "role": "user",
                    "content": f"工具执行结果:\n{tool_results_text}\n\n请基于这些结果给出完整的回答。"
                })

                current_iteration += 1
                continue

            break

        return messages

    def _non_stream_final_response(
            self,
            input_text: str,
            final_messages: list,
            **kwargs
    ):
        """
        非流式输出
        """
        final_response = self.llm.invoke(final_messages, **kwargs)
        self.add_message(Message(input_text, "user"))
        self.add_message(Message(final_response, "assistant"))

        return final_response

    def _stream_final_response(
            self,
            input_text: str,
            final_messages: list,
            **kwargs
    ) -> Iterator[str]:
        """
        流式输出
        """
        final_response = ""
        delta_response = self.llm.stream_invoke(final_messages, **kwargs)

        for dr in delta_response:
            final_response += dr
            yield dr

        self.add_message(Message(input_text, "user"))
        self.add_message(Message(final_response, "assistant"))
