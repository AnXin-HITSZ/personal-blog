"""语义记忆服务 - 跨会话长期记忆

采用"对话后评分-提取"机制：
1. 每次对话结束后，用 LLM 对该轮 (question, answer) 进行重要性评分（0-10）
2. 如果评分 >= 阈值且包含可长期记忆的信息，提取事实并合并到全局语义记忆文档
3. 新会话启动时，Agent 总是先读取该文档获取语义记忆

Redis 存储：
  Key: "semantic_memory:global"
  Type: STRING
  Value: 纯文本格式的语义记忆文档
"""

from typing import Optional, Tuple

from langchain_openai import ChatOpenAI
from loguru import logger
from redis.asyncio import Redis as AsyncRedis

from app.config import config
from app.core.redis_client import redis_manager

# Redis key
SEMANTIC_MEMORY_KEY = "semantic_memory:global"

# 重要性评分 Prompt
IMPORTANCE_SCORE_PROMPT = """You are an AI agent's long-term memory system. Analyze this conversation turn and determine if any information should be permanently remembered.

Information worth remembering includes:
- User preferences, likes, dislikes
- Personal background, role, expertise, goals
- Project details and technology choices
- Decisions, commitments, action items
- Personal context (timezone, language preference, etc.)

Conversation:
User: {question}
Assistant: {answer}

First, determine if this turn contains any information worth remembering (YES/NO).
If NO, respond with: "0||"
If YES, score its importance from 1-10 and extract the exact fact:

Importance scale:
1-3: Minor detail (remember if convenient)
4-6: Useful context (good to remember)
7-8: Important information (should definitely remember)
9-10: Critical information (must remember for all future interactions)

Respond with format: score||fact_to_remember"""


class SemanticMemory:
    """语义记忆服务 - 跨会话长期记忆"""

    def __init__(self):
        self._redis: Optional[AsyncRedis] = None

    async def _get_redis(self) -> AsyncRedis:
        """获取 Redis 客户端（延迟初始化）"""
        if self._redis is None:
            try:
                self._redis = await redis_manager.connect()
            except Exception as e:
                logger.error(f"语义记忆服务无法连接 Redis: {e}")
                raise
        return self._redis

    async def get_memory(self) -> str:
        """获取合并后的语义记忆文本

        Returns:
            str: 语义记忆文本，不存在则返回空字符串
        """
        if not config.semantic_memory_enabled:
            return ""

        try:
            redis = await self._get_redis()
            memory = await redis.get(SEMANTIC_MEMORY_KEY)
            return memory if memory else ""
        except Exception as e:
            logger.warning(f"获取语义记忆失败: {e}")
            return ""

    async def process_turn(
        self,
        question: str,
        answer: str,
        llm: ChatOpenAI,
    ) -> None:
        """分析对话轮次，提取语义记忆

        在对话的 (question, answer) 保存到 Redis 后调用。
        非关键路径——失败不影响主流程，仅记录 warning。

        Args:
            question: 用户问题
            answer: 助手回答
            llm: LLM 实例（用于评分和提取）
        """
        if not config.semantic_memory_enabled:
            return

        if not question or not answer:
            return

        try:
            # 1. 评分并提取事实
            score, fact = await self._score_importance(question, answer, llm)

            if score < config.semantic_memory_importance_threshold or not fact:
                logger.debug(f"语义记忆：跳过低分轮次 (score={score})")
                return

            logger.info(f"语义记忆：提取到重要事实 (score={score})")

            # 2. 合并到现有记忆
            existing = await self.get_memory()
            merged = self._merge_fact(existing, fact, score)

            # 3. 持久化
            redis = await self._get_redis()
            await redis.set(SEMANTIC_MEMORY_KEY, merged)
            logger.info(f"语义记忆已更新（共 {len(merged)} 字符）")

        except Exception as e:
            logger.warning(f"语义记忆处理失败: {e}")

    async def _score_importance(
        self,
        question: str,
        answer: str,
        llm: ChatOpenAI,
    ) -> Tuple[float, str]:
        """用 LLM 评分并提取事实

        Args:
            question: 用户问题
            answer: 助手回答
            llm: LLM 实例

        Returns:
            Tuple[float, str]: (重要性评分 0-10, 提取的事实文本)
            评分为 0 表示无值得记忆的内容，事实为空字符串
        """
        prompt = IMPORTANCE_SCORE_PROMPT.format(
            question=question[:1000],  # 限制长度避免超 context
            answer=answer[:2000],
        )

        try:
            response = await llm.ainvoke(prompt)
            text = response.content.strip() if hasattr(response, "content") else str(response).strip()

            # 解析 "score||fact" 格式
            if "||" not in text:
                return 0.0, ""

            score_str, fact = text.split("||", 1)
            score_str = score_str.strip()

            try:
                score = float(score_str)
            except ValueError:
                return 0.0, ""

            fact = fact.strip()
            if not fact:
                return 0.0, ""

            score = max(0.0, min(10.0, score))  # 限制在 0-10 范围
            return score, fact

        except Exception as e:
            logger.warning(f"语义记忆评分失败: {e}")
            return 0.0, ""

    def _merge_fact(self, existing_memory: str, new_fact: str, score: float) -> str:
        """将新事实合并到现有语义记忆文档

        Args:
            existing_memory: 现有语义记忆文本
            new_fact: 新提取的事实
            score: 重要性评分

        Returns:
            str: 合并后的语义记忆文档
        """
        # 如果已有记忆，检查是否已存在该事实（简单去重）
        if existing_memory:
            # 如果新事实已存在于记忆中，直接返回原文
            if new_fact in existing_memory:
                return existing_memory

            # 追加新事实
            lines = existing_memory.strip().split("\n")
            lines.append(f"- (重要性:{score:.0f}) {new_fact}")
            merged = "\n".join(lines)
        else:
            # 首次创建语义记忆文档
            merged = (
                "## Semantic Memory\n\n"
                f"- (重要性:{score:.0f}) {new_fact}"
            )

        # 检查是否超过最大事实数（统计以 "- " 开头的行）
        fact_lines = [l for l in merged.split("\n") if l.strip().startswith("- ")]
        if len(fact_lines) > config.semantic_memory_max_facts:
            # 删除最早的事实（保留前两行 header + 最近的事实）
            header = merged.split("\n")[:2]
            recent_facts = fact_lines[-(config.semantic_memory_max_facts):]
            merged = "\n".join(header + recent_facts)
            logger.info(f"语义记忆：超过最大事实数，已裁剪至 {config.semantic_memory_max_facts} 条")

        return merged

    async def clear_memory(self) -> None:
        """清除所有语义记忆"""
        try:
            redis = await self._get_redis()
            await redis.delete(SEMANTIC_MEMORY_KEY)
            logger.info("语义记忆已清除")
        except Exception as e:
            logger.warning(f"清除语义记忆失败: {e}")


# 全局单例
semantic_memory = SemanticMemory()
