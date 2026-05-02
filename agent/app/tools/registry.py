import re
from typing import Optional
import json

from app.tools.base import Tool


class ToolRegistry:
    """
    Agents 工具注册表
    """

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register_tool(self, tool: Tool):
        """
        注册 Tool 对象
        """
        self._tools[tool.name] = tool
        print(f"工具 '{tool.name}' 已注册")

    def get_tools_description(self) -> str:
        """
        获取所有可用工具的格式化描述字符串
        """
        description = []

        for tool in self._tools.values():
            params = tool.get_parameters()
            if params:
                param_lines = []
                for p in params:
                    opt = " (可选)" if not p.required else ""
                    param_lines.append(f"      {p.name} ({p.type}){opt}: {p.description}")
                param_str = "\n" + "\n".join(param_lines)
            else:
                param_str = " (无参数)"
            description.append(f"- {tool.name}: {tool.description}{param_str}")

        return "\n".join(description) if description else "暂无可用工具"

    def get_tool(self, name: str) -> Optional[Tool]:
        """
        获取 Tool 对象
        """
        return self._tools.get(name)

    def parse_tool_calls(self, text: str) -> list:
        """
        解析文本中的工具调用
        """
        pattern = r'\[TOOL_CALL:([^:]*):([^\]]*)\]'
        matches = re.findall(pattern, text)

        tool_calls = []
        for tool_name, parameters in matches:
            tool_calls.append({
                'tool_name': tool_name.strip(),
                'parameters': parameters.strip(),
                'original': f'[TOOL_CALL:{tool_name}:{parameters}]'
            })

        return tool_calls

    def execute_tool(self, name: str, tool_input: str) -> str:
        """
        执行某一个工具，返回 str 字符串
        """
        response = ""

        if name in self._tools:
            tool = self._tools[name]
            if isinstance(tool_input, str):
                try:
                    parameters = json.loads(tool_input)
                except json.JSONDecodeError:
                    parameters = {"input": tool_input}
            elif isinstance(tool_input, dict):
                parameters = tool_input
            else:
                parameters = {"input": str(tool_input)}
            response = tool.run(parameters)
        else:
            response = f"未找到名为 '{name}' 的工具"

        return response
