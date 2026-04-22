from datetime import datetime
from typing import Dict, Any, List

from app.tools.base import Tool, ToolParameter


class CurrentTimeTool(Tool):
    """
    获取当前时间
    """
    def __init__(self):
        super().__init__(
            name="get_current_time",
            description="获取当前系统（本地时区）的日期和时间"
        )

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="format",
                type="string",
                description="时间格式化字符串，例如 '%Y-%m-%d %H:%M:%S'，不填则使用默认格式",
                required=False,
                default="%Y-%m-%d %H:%M:%S",
            )
        ]

    def run(self, parameters: Dict[str, Any]) -> str:
        try:
            format_str = parameters.get("format", "%Y-%m-%d %H:%M:%S")
            now = datetime.now()

            return f"当前时间: {now.strftime(format_str)}"
        except Exception as e:
            return f"获取时间失败: {str(e)}"
