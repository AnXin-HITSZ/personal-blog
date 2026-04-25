from .current_time_tool import CurrentTimeTool

AVAILABLE_TOOLS = [
    CurrentTimeTool(),
]

TOOL_MAP = {
    tool.name: tool for tool in AVAILABLE_TOOLS
}
