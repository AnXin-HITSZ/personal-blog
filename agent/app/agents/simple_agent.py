from collections.abc import Iterator
from typing import Optional, Dict, List, Any, Union, Tuple

from app.core.agent import Agent
from app.core.llm import AgentsLLM
from app.tools.registry import ToolRegistry


class SimpleAgent(Agent):
    """
    简单的对话 Agent，支持工具调用
    """

    def __init__(
            self,
            name: str,
            llm: AgentsLLM,
            tool_registry: Optional['ToolRegistry'],
            memory_context: List[Tuple[int, Dict[str, str]]]
    ):
        """
        初始化 SimpleAgent
        """
        super().__init__(
            name,
            llm,
            tool_registry
        )
        self.memory_context = memory_context

    def run(
            self,
            input_text: str,
            max_tool_iterations: int = 3,
            stream=True
    ) -> Union[str, Iterator[str]]:
        """
        运行 SimpleAgent
        """
        enhanced_system_prompt = self._get_enhanced_system_prompt()
        messages = self._build_messages(enhanced_system_prompt, input_text)

        final_messages = self._execute_tool_loop(messages, max_tool_iterations)

        if stream:
            return self._stream_final_response(final_messages)
        else:
            return self._non_stream_final_response(final_messages)

    def _get_enhanced_system_prompt(self) -> str:
        """
        构建增强的系统提示词，包含工具信息
        """
        base_prompt = ""

        tools_description = self.tool_registry.get_tools_description()
        if not tools_description or tools_description == "暂无可用工具":
            return base_prompt

        base_prompt  ="""你是一个有用的AI助手。
        
        ## 可用工具
        你可以使用以下工具来帮助回答问题:
        {tools_description}
        
        ## 工具调用格式
        当需要使用工具时，请使用以下格式:
        `[TOOL_CALL:{{tool_name}}:{{parameters}}]`
        要求:
        1. {{tool_name}} 替换为工具名称
        2. {{parameters}} 替换为 JSON 格式的参数字符串
        3. 如果工具不需要参数，parameters 部分留空即可，例如: `[TOOL_CALL:get_current_time:]`
        4. 如果只有一个简单参数，也可以直接填值，例如: `[TOOL_CALL:search:Python]`
        
        工具调用结果会自动插入到对话中，然后你可以基于结果继续回答。
        
        ## 相关对话记忆
        {memory_context}
        
        现在开始你的回答:
        """

        str_memory_content = ""
        for mem in self.memory_context:
            timestamp, msg = mem
            if msg["role"] == "error":
                str_memory_content = msg["content"]
                break
            str_memory_content += f"- [{timestamp}] {msg['role']}: {msg['content']}"

        if self.memory_context:
            if not tools_description or tools_description == "暂无可用工具":
                base_prompt = base_prompt.replace(
                    "{tools_description}",
                    "暂无可用工具。请直接使用 Finish[你的完整答案] 来回答用户问题，禁止调用工具。"
                )
                base_prompt = base_prompt.format(
                    memory_context=str_memory_content
                )
            else:
                base_prompt = base_prompt.format(
                    tools_description=tools_description,
                    memory_context=str_memory_content
                )

        return base_prompt

    def _execute_tool_loop(
            self,
            messages: List[Dict[str, Any]],
            max_tool_iterations: int
    ) -> list:
        """
        运行工具调用，返回最终的 messages 列表
        """
        current_iteration = 0

        while current_iteration < max_tool_iterations:
            response = self.llm.invoke(messages)

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
            final_messages: list
    ):
        """
        非流式输出
        """
        final_response = self.llm.invoke(final_messages)

        return final_response

    def _stream_final_response(
            self,
            final_messages: list
    ) -> Iterator[str]:
        """
        流式输出
        """
        final_response = ""
        delta_response = self.llm.stream_invoke(final_messages)

        for dr in delta_response:
            final_response += dr
            yield dr
