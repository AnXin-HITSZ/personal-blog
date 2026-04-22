import os

from app.agents.simple_agent import SimpleAgent
from app.core.llm import AgentsLLM
from app.tools.default_tools import CurrentTimeTool
from app.tools.registry import ToolRegistry
from app.tools.base import Tool

LLM_MODEL_ID = os.environ.get("LLM_MODEL_ID")
LLM_API_KEY = os.environ.get("LLM_API_KEY")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL")

llm = AgentsLLM(
    LLM_MODEL_ID,
    LLM_API_KEY,
    LLM_BASE_URL
)

tool_registry = ToolRegistry()
tool_registry.register_tool(CurrentTimeTool())

agent = SimpleAgent(
    LLM_MODEL_ID,
    llm,
    tool_registry
)

response_generator = agent.run("你好！你知道当前时间吗？", 3, True)

for token in response_generator:
    print(token, end="", flush=True)
