import time
import json
from typing import List, Dict, Tuple, Any
import math
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import jieba
import redis
from dataclasses import dataclass, field
from datetime import datetime

from app.memory.utils.tokenizer import jieba_tokenizer, STOPWORDS


@dataclass
class MemoryItem:
    """
    单条记忆的数据结构
    """
    id: str = field(default_factory=lambda: f"men_{int(time.time() * 1000000)}")
    role: str = "user"
    content: str = ""
    importance: float = 0.5
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_timestamp(self) -> datetime:
        """
        将时间戳转换为人类可读的日期时间格式
        """
        return datetime.fromtimestamp(self.timestamp)

    def to_json(self) -> str:
        """
        序列化为完整的 JSON（存入 Redis Hash）
        """
        return json.dumps({
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "importance": self.importance,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "MemoryItem":
        """
        从 Redis Hash 反序列化
        """
        data = json.loads(json_str)
        return cls(**data)

@dataclass
class MemoryConfig:
    """
    工作记忆的配置类
    """
    redis_url: str
    memory_capacity: int = 50
    ttl_seconds: int = 120
    default_importance: float = 0.5

class WorkingMemory:
    """
    工作记忆实现
    """

    def __init__(
            self,
            config: MemoryConfig
    ):
        """
        初始化工作记忆
        """
        self.config = config
        self.redis = redis.from_url(self.config.redis_url, decode_responses=True)
        self.max_capacity = self.config.memory_capacity
        self.ttl_seconds = config.ttl_minutes

    def _key_meta(self, session_id: str) -> str:
        """
        存储记忆元数据的 Hash Key
        """
        return f"memory:meta:{session_id}"

    def _key_index(self, session_id: str) -> str:
        """
        存储记忆 ID 索引的 List Key
        """
        return f"memory:index:{session_id}"

    def add(self, session_id: str, item: MemoryItem) -> str:
        """
        添加一条记忆
        """
        key_meta = self._key_meta(session_id)
        key_index = self._key_index(session_id)

        self.redis.hset(key_meta, item.id, item.to_json())
        self.redis.rpush(key_index, item.id)

        current_length = self.redis.llen(key_index)
        if current_length > self.max_capacity:
            self._remove_lowest_priority_memory(session_id)

        self.redis.expire(key_meta, self.ttl_seconds)
        self.redis.expire(key_index, self.ttl_seconds)

        return item.id

    def add_message(
            self,
            session_id: str,
            role: str,
            content: str,
            importance: float
    ) -> str:
        """
        添加消息
        """
        item = MemoryItem(
            role=role,
            content=content,
            importance=importance
        )
        return self.add(session_id, item)

    def get_all(self, session_id: str) -> List[MemoryItem]:
        """
        获取所有记忆（按时间顺序）
        """
        key_meta = self._key_meta(session_id)
        key_index = self._key_index(session_id)

        memory_ids = self.redis.lrange(key_index, 0, -1)

        if not memory_ids:
            return []

        memory_jsons = self.redis.hmget(key_meta, memory_ids)

        memories = []
        for js in memory_jsons:
            if js:
                memories.append(MemoryItem.from_json(js))

        return memories

    def get_history(self, session_id: str, limit: int = 15) -> List[Dict[str, str]]:
        """
        获取最近 N 条历史
        """
        pass

    def clear(self, session_id: str):
        """
        清空所有记忆
        """
        self.redis.delete(self._key_meta(session_id))
        self.redis.delete(self._key_index(session_id))

    def _remove_lowest_priority_memory(self, session_id: str):
        """
        删除优先级最低的记忆
        """
        all_memories = self.get_all(session_id)
        if not all_memories:
            return

        scored_memories = []
        for mem in all_memories:
            time_decay = self._calculate_time_decay(mem.timestamp)
            score = mem.importance * time_decay
            scored_memories.append((score, mem))

        scored_memories.sort(key=lambda x: x[0])
        lowest_score_memory = scored_memories[0][1]

        key_meta = self._key_meta(session_id)
        key_index = self._key_index(session_id)

        self.redis.hdel(key_meta, lowest_score_memory.id)
        self.redis.lrem(key_index, 1, lowest_score_memory.id)

    def _calculate_time_decay(self, timestamp: float) -> float:
        """
        计算时间衰减因子
        """
        age_seconds = time.time() - timestamp
        age_minutes = age_seconds / 60

        half_file = 60
        decay = math.exp(-age_minutes / half_file)

        return max(decay, 0.01)

    def retrieve(self, session_id: str, query: str, limit: int = 5) -> List[Tuple[int, Dict[str, str]]]:
        """
        混合检索: TF-IDF 向量化 + 关键词匹配
        """
        all_memories = self.get_all(session_id)

        if not all_memories:
            return [(
                0,
                {
                    "role": "error",
                    "content": "暂无相关对话记忆"
                }
            )]

        vector_scores = self._try_tfidf_search(query, all_memories)

        scored_memories = []
        for memory in all_memories:
            vector_score = vector_scores.get(memory.id, 0.0)
            keyword_score  = self._calculate_keyword_score(query, memory.content)

            if vector_score > 0:
                base_relevance = vector_score * 0.7 + keyword_score * 0.3
            else:
                base_relevance = keyword_score

            time_decay = self._calculate_time_decay(memory.timestamp)
            importance_weight = 0.8 + (memory.importance * 0.4)

            final_score = base_relevance * time_decay * importance_weight

            if final_score > 0:
                scored_memories.append((final_score, memory))

        scored_memories.sort(key=lambda x: x[0], reverse=True)

        relevant = [memory for _, memory in scored_memories[:limit]]

        # result = "以下是相关的对话历史：\n"
        # for mem in relevant:
        #     dt = mem.get_timestamp_datetime().strftime("%H:%M")
        #     result += f"- [{dt}] {mem.role}: {mem.content}\n"

        result = []
        for mem in relevant:
            dt = mem.get_timestamp().strftime("%H:%M")
            result.append((
                dt,
                {
                    "role": mem.role,
                    "content": mem.content
                }
            ))

        return result

    def _try_tfidf_search(self, query: str, memories: List[MemoryItem]) -> Dict[str, float]:
        """
        尝试 TF-IDF 搜索，如果失败则返回空字典
        """
        if len(memories) < 2:
            return {}

        try:
            self._update_tfidf_index(memories)
            query_vec = self._tfidf_vectorizer.transform([query])
            similarities = cosine_similarity(query_vec, self._tfidf_matrix)[0]

            return {
                memories[i].id: float(similarities[i])
                for i in range(len(memories))
            }
        except Exception as e:
            print(f"TF-IDF 搜索出错: {e}")
            return {}


    def _update_tfidf_index(self, memories: List[MemoryItem]):
        """
        更新使用 jieba 分词的 TF-IDF 索引（带缓存机制，避免每次都重新计算）
        """
        if hasattr(self, '_tfidf_matrix') and self._tfidf_matrix is not None:
            if len(memories) == self._last_tfidf_update_count:
                return

        docs = [mem.content for mem in memories]
        ids = [mem.id for mem in memories]

        self._tfidf_vectorizer = TfidfVectorizer(
            tokenizer=jieba_tokenizer,
            token_pattern=None,
            stop_words=list(STOPWORDS)
        )

        self._tfidf_matrix = self._tfidf_vectorizer.fit_transform(docs)
        self._last_tfidf_update_count = len(memories)

    def _calculate_keyword_score(self, query: str, content: str) -> float:
        """
        计算关键词匹配分数: 使用 jieba 分词 + 词交集匹配
        """
        if not query or not content:
            return 0.0

        query_words = jieba.lcut(query.lower())
        content_words = jieba.lcut(content.lower())

        def is_valid_word(w: str) -> bool:
            """
            过滤停用词和过短的词
            """
            return len(w) >= 1 and w not in STOPWORDS and w.strip() != ""

        query_words_filtered = [w for w in query_words if is_valid_word(w)]
        content_words_set = set([w for w in content_words if is_valid_word(w)])

        if not query_words_filtered:
            return 0.0

        score = 0.0
        matched_words = []

        for word in query_words_filtered:
            if word in content_words_set:
                matched_words.append(word)
                weight = 0.2 + (len(word) * 0.1)
                score += weight

        query_lower = query.lower()
        content_lower = content.lower()
        if any(kw in content_lower for kw in query_words_filtered if len(kw) >= 2):
            score += 0.3

        final_score = min(score, 1.0)

        if matched_words:
            print(f"[匹配] 查询: {query} | 记忆: {content} |匹配词: {matched_words} | 分数: {final_score:.2f}")

        return final_score
