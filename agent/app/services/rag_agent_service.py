"""RAG Agent 服务 - 基于 LangGraph 的智能代理

使用 langchain_openai 的 ChatOpenAI 调用 DeepSeek 模型（OpenAI 兼容接口），
支持真正的流式输出和更好的模型适配。

架构说明：
  不再使用 MemorySaver checkpointer，改为 query/query_stream 方法
  自行管理对话历史。历史消息通过 conversation_memory 持久化到 Redis，
  确保服务重启后会话不丢失，同时避免 tool 消息污染发送给 LLM 的消息列表。
"""

from typing import Any, AsyncGenerator, Dict

from langchain.agents import create_agent
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from loguru import logger
from langchain_openai import ChatOpenAI

from app.config import config
from app.services.conversation_memory import conversation_memory
from app.tools import get_current_time, retrieve_knowledge
from app.agent.mcp_client import get_mcp_client_with_retry


class RagAgentService:
    """RAG Agent 服务 - 使用 LangGraph + ChatOpenAI(DeepSeek) 原生集成"""

    def __init__(self, streaming: bool = True):
        """初始化 RAG Agent 服务

        Args:
            streaming: 是否启用流式输出，默认为 True
        """
        self.streaming = streaming
        self.system_prompt = self._build_system_prompt()

        self.model = ChatOpenAI(
            model=config.llm_model_id,
            api_key=config.llm_api_key,
            base_url=config.llm_base_url,
            temperature=0.7,
            streaming=streaming,
        )

        # 定义基础工具
        self.tools = [retrieve_knowledge, get_current_time]

        # Agent 实例（延迟初始化）
        self.agent = None
        self._agent_initialized = False

        logger.info(
            f"RAG Agent 服务初始化完成 (ChatOpenAI + DeepSeek), "
            f"model={config.llm_model_id}, streaming={streaming}"
        )

    async def _initialize_agent(self):
        """异步初始化 Agent（包括 MCP 工具）"""
        if self._agent_initialized:
            return

        # 尝加载 MCP 工具（非关键路径，失败不阻塞）
        try:
            mcp_client = await get_mcp_client_with_retry()
            mcp_tools = await mcp_client.get_tools()
            logger.info(f"成功加载 {len(mcp_tools)} 个 MCP 工具")
        except Exception as e:
            logger.warning(f"MCP 工具加载失败，仅使用内置工具: {e}")
            mcp_tools = []

        # 合并所有工具
        all_tools = self.tools + (mcp_tools if mcp_tools else [])

        # 注意：不传 checkpointer，每轮 Agent 调用独立。
        # 历史消息由 conversation_memory (Redis) 管理，在调用前拼接到 messages 中。
        self.agent = create_agent(
            self.model,
            tools=all_tools,
            checkpointer=None,
        )

        self._agent_initialized = True

        if all_tools:
            tool_names = [
                tool.name if hasattr(tool, "name") else str(tool)
                for tool in all_tools
            ]
            logger.info(f"可用工具列表: {', '.join(tool_names)}")

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        from textwrap import dedent

        return dedent("""
            你是一个专业的AI助手，能够使用多种工具来帮助用户解决问题。

            工作原则:
            1. 理解用户需求，选择合适的工具来完成任务
            2. 当需要获取实时信息或专业知识时，主动使用相关工具
            3. 基于工具返回的结果提供准确、专业的回答
            4. 如果工具无法提供足够信息，请诚实地告知用户

            回答要求:
            - 保持友好、专业的语气
            - 回答简洁明了，重点突出
            - 基于事实，不编造信息
            - 如有不确定的地方，明确说明

            请根据用户的问题，灵活使用可用工具，提供高质量的帮助。
        """).strip()

    async def _build_messages_with_history(
        self, question: str, session_id: str
    ) -> list[BaseMessage]:
        """从 Redis 加载历史消息并构建完整的 messages 列表。

        Args:
            question: 用户当前问题
            session_id: 会话 ID

        Returns:
            list[BaseMessage]: System + 历史对话 + 当前问题
        """
        history = await conversation_memory.get_messages(session_id)

        messages: list[BaseMessage] = [
            SystemMessage(content=self.system_prompt)
        ]

        for msg in history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

        messages.append(HumanMessage(content=question))
        return messages

    async def query(self, question: str, session_id: str) -> str:
        """非流式处理用户问题（一次性返回完整答案）

        Args:
            question: 用户问题
            session_id: 会话 ID

        Returns:
            str: 完整答案
        """
        try:
            await self._initialize_agent()

            logger.info(f"[会话 {session_id}] RAG Agent 收到查询（非流式）: {question}")

            # 1. 从 Redis 加载历史消息，构建完整消息列表
            messages = await self._build_messages_with_history(question, session_id)

            # 2. 调用 Agent（无 checkpointer，单轮独立）
            result = await self.agent.ainvoke({"messages": messages})

            # 3. 提取最终答案
            messages_result = result.get("messages", [])
            if messages_result:
                last_message = messages_result[-1]
                answer = (
                    last_message.content
                    if hasattr(last_message, "content")
                    else str(last_message)
                )
            else:
                answer = ""

            logger.info(f"[会话 {session_id}] RAG Agent 查询完成（非流式）")

            # 4. 保存到 Redis
            await conversation_memory.add_message(session_id, "user", question)
            if answer:
                await conversation_memory.add_message(session_id, "assistant", answer)

            return answer

        except Exception as e:
            logger.error(f"[会话 {session_id}] RAG Agent 查询失败（非流式）: {e}")
            raise

    async def query_stream(
        self,
        question: str,
        session_id: str,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式处理用户问题（逐步返回答案片段）

        Args:
            question: 用户问题
            session_id: 会话 ID

        Yields:
            Dict[str, Any]: 流式事件
                - type: "content" | "tool_call" | "complete" | "error"
                - data: 具体内容
        """
        try:
            await self._initialize_agent()

            logger.info(f"[会话 {session_id}] RAG Agent 收到查询（流式）: {question}")

            # 1. 从 Redis 加载历史消息，构建完整消息列表
            messages = await self._build_messages_with_history(question, session_id)

            # 2. 流式调用 Agent
            content_accumulator = ""
            announced_tool_calls: set[str] = set()

            async for chunk, metadata in self.agent.astream(
                {"messages": messages},
                stream_mode="messages",
            ):
                # ── AIMessageChunk: 可能是文本块或 tool_call 块 ──
                if isinstance(chunk, AIMessageChunk):
                    # 检测工具调用（通过 tool_call_chunks）
                    tool_chunks = getattr(chunk, "tool_call_chunks", None) or []
                    for tc in tool_chunks:
                        tc_id = tc.get("id", "") or tc.get("index", "")
                        name = tc.get("name", "")
                        if name and tc_id not in announced_tool_calls:
                            announced_tool_calls.add(tc_id)
                            yield {
                                "type": "tool_call",
                                "data": {
                                    "name": name,
                                    "status": "start",
                                },
                            }

                    # 文本内容
                    text_content = chunk.content or ""
                    if text_content:
                        content_accumulator += text_content
                        yield {
                            "type": "content",
                            "data": text_content,
                        }

                # ── ToolMessage: 工具执行完成 ──
                elif isinstance(chunk, ToolMessage):
                    yield {
                        "type": "tool_call",
                        "data": {
                            "name": getattr(chunk, "name", "") or "unknown_tool",
                            "status": "end",
                            "result": (chunk.content or "")[:300],
                        },
                    }

            logger.info(f"[会话 {session_id}] RAG Agent 查询完成（流式）")

            # 3. 保存到 Redis
            await conversation_memory.add_message(session_id, "user", question)
            if content_accumulator:
                await conversation_memory.add_message(
                    session_id, "assistant", content_accumulator
                )

            yield {"type": "complete"}

        except Exception as e:
            logger.error(f"[会话 {session_id}] RAG Agent 查询失败（流式）: {e}")
            yield {"type": "error", "data": str(e)}
            raise

    async def get_session_history(self, session_id: str) -> list:
        """获取会话历史（从 Redis 读取）

        Args:
            session_id: 会话 ID

        Returns:
            list: 消息历史列表
        """
        return await conversation_memory.get_messages(session_id)

    async def clear_session(self, session_id: str) -> bool:
        """清空会话历史（从 Redis 删除）

        Args:
            session_id: 会话 ID

        Returns:
            bool: 是否成功
        """
        return await conversation_memory.clear_session(session_id)

    def get_message_count(self, session_id: str) -> int:
        """获取会话消息数量（仅用于回退，不抛异常）"""
        try:
            import asyncio
            return asyncio.run(conversation_memory.get_message_count(session_id))
        except Exception:
            return 0

    async def cleanup(self):
        """清理资源"""
        try:
            logger.info("清理 RAG Agent 服务资源...")
            logger.info("RAG Agent 服务资源已清理")
        except Exception as e:
            logger.error(f"清理资源失败: {e}")


# 全局单例
rag_agent_service = RagAgentService(streaming=True)
