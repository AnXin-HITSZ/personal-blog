"""记忆编排器 - 管理对话记忆的完整生命周期

职责：
1. 构建 LLM 上下文消息列表（语义记忆 + 对话摘要 + 最近消息 + 当前问题）
2. 对话结束后执行记忆维护（压缩检查 + 语义提取）

依赖：
- ConversationMemory: Redis 对话历史存取、摘要存取、消息裁剪
- SemanticMemory: 跨会话长期记忆的评分、提取、合并
"""

from typing import List

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from loguru import logger

from app.config import config
from app.services.conversation_memory import conversation_memory
from app.services.semantic_memory import semantic_memory

# 摘要生成的 LLM Prompt
SUMMARY_PROMPT = """You are summarizing a conversation history for an AI assistant.
Compress the following conversation into a concise summary that preserves:
- Key user questions and intents
- Important information the user shared (preferences, context, goals)
- Solutions or answers provided
- Decisions made

Keep the summary to at most {max_words} words. Focus on information that
remains relevant for future conversation turns.

Conversation to summarize:
{formatted_messages}

Summary:"""


class MemoryOrchestrator:
    """记忆编排器"""

    def __init__(self):
        self.conversation = conversation_memory
        self.semantic = semantic_memory

    async def build_context_messages(
        self,
        base_system_prompt: str,
        session_id: str,
        question: str,
    ) -> List[BaseMessage]:
        """构建完整的 LLM 上下文消息列表

        组装顺序：
        1. SystemMessage (基础 system prompt)
        2. SystemMessage (语义记忆上下文, 如果存在)
        3. SystemMessage (对话摘要, 如果存在)
        4. HumanMessage/AIMessage pairs (最近的未压缩消息)
        5. HumanMessage (当前问题)

        Args:
            base_system_prompt: 基础系统提示词
            session_id: 会话 ID
            question: 当前用户问题

        Returns:
            List[BaseMessage]: 完整的消息列表
        """
        messages: List[BaseMessage] = [
            SystemMessage(content=base_system_prompt)
        ]

        # 1. 加载语义记忆（跨会话长期记忆）
        try:
            semantic_text = await self.semantic.get_memory()
            if semantic_text:
                messages.append(SystemMessage(
                    content=f"以下是我从历史对话中了解到的关于用户的信息：\n{semantic_text}"
                ))
        except Exception as e:
            logger.warning(f"加载语义记忆失败: {e}")

        # 2. 加载对话摘要（当前会话早期部分的压缩）
        try:
            summary_text = await self.conversation.get_summary(session_id)
            if summary_text:
                messages.append(SystemMessage(
                    content=f"以下是本会话早期对话的摘要：\n{summary_text}"
                ))
        except Exception as e:
            logger.warning(f"加载对话摘要失败: {e}")

        # 3. 加载最近的历史消息
        try:
            history = await self.conversation.get_messages(session_id)
            for msg in history:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))
        except Exception as e:
            logger.warning(f"加载历史消息失败: {e}")

        # 4. 当前问题
        messages.append(HumanMessage(content=question))

        return messages

    async def run_post_turn_maintenance(
        self,
        session_id: str,
        question: str,
        answer: str,
        llm: ChatOpenAI,
    ) -> None:
        """对话后记忆维护

        在每轮对话的 (question, answer) 保存到 Redis 后调用。
        非关键路径——失败不影响主流程，仅记录 warning。

        执行顺序：
        1. 压缩检查：如果消息数超过阈值，对最早的消息生成摘要并裁剪
        2. 语义提取：对当前轮次进行重要性评分，提取事实到长期记忆

        Args:
            session_id: 会话 ID
            question: 用户问题
            answer: 助手回答
            llm: LLM 实例
        """
        try:
            await self._compress_if_needed(session_id, llm)
        except Exception as e:
            logger.warning(f"记忆压缩失败: {e}")

        try:
            await self.semantic.process_turn(question, answer, llm)
        except Exception as e:
            logger.warning(f"语义提取失败: {e}")

    async def _compress_if_needed(
        self,
        session_id: str,
        llm: ChatOpenAI,
    ) -> None:
        """检查压缩阈值并在需要时执行压缩

        算法：
        1. 获取当前消息数
        2. 如果超过阈值，计算需要压缩的条数
        3. 读取最早的消息
        4. 调用 LLM 生成摘要
        5. 保存摘要到 Redis
        6. 裁剪消息列表

        Args:
            session_id: 会话 ID
            llm: LLM 实例
        """
        count = await self.conversation.get_message_count(session_id)
        max_messages = config.memory_max_message_pairs * 2
        threshold_count = int(max_messages * config.memory_summary_threshold_ratio)

        if count < threshold_count:
            return

        logger.info(
            f"会话 {session_id}: 消息数 {count} 超过阈值 {threshold_count}，触发压缩"
        )

        # 计算需要压缩的条数（保留最新的 keep_ratio 比例）
        keep_count = int(max_messages * config.memory_keep_ratio)
        # 确保 keep_count 为偶数（保持 user/assistant 成对）
        keep_count = keep_count if keep_count % 2 == 0 else keep_count + 1

        # 确保压缩后至少保留 2 条
        compress_count = count - keep_count
        if compress_count < 2:
            compress_count = count - 2
            if compress_count < 2:
                logger.debug("消息数太少，跳过压缩")
                return

        # 确保 compress_count 为偶数
        compress_count = compress_count if compress_count % 2 == 0 else compress_count - 1

        try:
            # 读取最早的消息
            oldest_messages = await self.conversation.get_messages_range(
                session_id, 0, compress_count - 1
            )

            if not oldest_messages:
                return

            # 生成摘要
            summary = await self._generate_summary(oldest_messages, llm)
            if not summary:
                logger.warning("摘要生成为空，跳过压缩")
                return

            # 保存摘要
            await self.conversation.save_summary(session_id, summary)

            # 裁剪消息（保留最近的 keep_count 条）
            new_count = await self.conversation.trim_messages(session_id, keep_count)

            logger.info(
                f"会话 {session_id}: 压缩完成，"
                f"压缩了 {compress_count} 条消息，"
                f"当前消息数 {new_count}"
            )

        except Exception as e:
            logger.warning(f"会话 {session_id} 压缩失败: {e}")

    async def _generate_summary(
        self,
        messages: list,
        llm: ChatOpenAI,
    ) -> str:
        """调用 LLM 生成会话摘要

        Args:
            messages: 消息列表（最早的消息）
            llm: LLM 实例

        Returns:
            str: 生成的摘要文本，失败返回空字符串
        """
        # 格式化消息
        formatted = ""
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            # 截断过长的消息
            if len(content) > 500:
                content = content[:500] + "..."
            formatted += f"[{role}]: {content}\n\n"

        if not formatted.strip():
            return ""

        prompt = SUMMARY_PROMPT.format(
            formatted_messages=formatted,
            max_words=config.memory_summary_max_words,
        )

        try:
            response = await llm.ainvoke(prompt)
            summary = response.content.strip() if hasattr(response, "content") else str(response).strip()
            return summary
        except Exception as e:
            logger.warning(f"摘要生成失败: {e}")
            return ""


# 全局单例
memory_orchestrator = MemoryOrchestrator()
