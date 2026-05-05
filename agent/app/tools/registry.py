import re
import json
from typing import Optional

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

        支持两种格式:
        1. [TOOL_CALL:工具名:JSON参数] （标准格式）
        2. 工具名({"key": "value"}) （宽松格式）
        """
        tool_calls = []

        # 格式1: [TOOL_CALL:工具名:参数]
        idx = 0
        while True:
            start = text.find('[TOOL_CALL:', idx)
            if start == -1:
                break

            name_start = start + len('[TOOL_CALL:')
            colon_pos = text.find(':', name_start)
            if colon_pos == -1:
                break

            tool_name = text[name_start:colon_pos].strip()

            # 用大括号平衡查找 JSON 结束位置
            json_start = text.find('{', colon_pos + 1)
            if json_start == -1:
                idx = colon_pos + 1
                continue

            depth = 0
            json_end = -1
            for i in range(json_start, len(text)):
                if text[i] == '{':
                    depth += 1
                elif text[i] == '}':
                    depth -= 1
                    if depth == 0:
                        json_end = i
                        break

            if json_end == -1:
                idx = json_start + 1
                continue

            # 确认后面跟着 ]
            if json_end + 1 < len(text) and text[json_end + 1] == ']':
                parameters = text[json_start:json_end + 1]
                tool_calls.append({
                    'tool_name': tool_name,
                    'parameters': parameters,
                    'original': text[start:json_end + 2],
                })
                idx = json_end + 2
            else:
                idx = json_end + 1

        # 格式2: 工具名({"key": "value"}) — 宽松匹配（仅当格式1无结果时尝试）
        if not tool_calls:
            for match in re.finditer(r'(\w+)\s*\(', text):
                tool_name = match.group(1).strip()
                if tool_name not in self._tools:
                    continue

                paren_start = match.end()
                json_start = text.find('{', paren_start)
                if json_start == -1:
                    continue

                depth = 0
                json_end = -1
                for i in range(json_start, len(text)):
                    if text[i] == '{':
                        depth += 1
                    elif text[i] == '}':
                        depth -= 1
                        if depth == 0:
                            json_end = i
                            break

                if json_end == -1:
                    continue

                # 确认后面跟着 )
                if json_end + 1 < len(text) and text[json_end + 1] == ')':
                    parameters = text[json_start:json_end + 1]
                    tool_calls.append({
                        'tool_name': tool_name,
                        'parameters': parameters,
                        'original': text[match.start():json_end + 2],
                    })

        return tool_calls

    def _try_extract_json_parameters(self, raw: str) -> Optional[dict]:
        """
        尝试从字符串中提取 JSON 参数。

        策略：
        1. 直接 json.loads
        2. 找到第一个 { 和匹配的 }，提取并解析
        3. 如果还是失败，返回 None
        """
        raw = raw.strip()

        # 策略1: 直接解析
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        # 策略2: 去除外层引号（LLM 有时会多包裹一层）
        if (raw.startswith('"') and raw.endswith('"')) or \
           (raw.startswith("'") and raw.endswith("'")):
            try:
                return json.loads(raw[1:-1])
            except json.JSONDecodeError:
                pass

        # 策略3: 用大括号平衡查找 JSON 对象
        try:
            start = raw.index('{')
            depth = 0
            json_chars = []
            for c in raw[start:]:
                json_chars.append(c)
                if c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0:
                        candidate = ''.join(json_chars)
                        return json.loads(candidate)
        except (ValueError, json.JSONDecodeError):
            pass

        return None

    def execute_tool(self, name: str, tool_input: str) -> str:
        """
        执行某一个工具，返回 str 字符串
        """
        if name not in self._tools:
            return f"未找到名为 '{name}' 的工具"

        tool = self._tools[name]

        if isinstance(tool_input, str):
            parameters = self._try_extract_json_parameters(tool_input)
            if parameters is None:
                # 所有 JSON 解析方式都失败了
                # 尝试从原始文本中用简单方式提取关键参数
                return (
                    f"❌ 工具参数格式错误：JSON 解析失败。\n"
                    f"原因：参数内容中包含未转义的双引号（\"）或特殊字符。\n"
                    f"请确保：\n"
                    f"1. 内容中的双引号使用 \\\" 转义\n"
                    f"2. 内容中的换行使用 \\n\n"
                    f"3. 使用正确的 JSON 格式：{{\"key\": \"value\"}}\n"
                    f"格式示例：[TOOL_CALL:{name}:{{\"param1\": \"value1\"}}]"
                )
        elif isinstance(tool_input, dict):
            parameters = tool_input
        else:
            parameters = {"input": str(tool_input)}

        return tool.run(parameters)
