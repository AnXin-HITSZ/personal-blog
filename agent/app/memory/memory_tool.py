from typing import Union, List, Tuple, Dict

from app.memory.working_memory import MemoryItem
from app.memory.manager import UnifiedMemoryManager
from app.memory import WorkingMemory
from app.memory import EpisodicMemory


MemoryInstance = Union[WorkingMemory, EpisodicMemory]

class MemoryTool:
    """
    记忆系统统一接口
    """

    def __init__(
            self,
            memory_manager: UnifiedMemoryManager
    ):
        self.working_memory: WorkingMemory = memory_manager.memory_types['working_memory']
        self.episodic_memory: EpisodicMemory = memory_manager.memory_types['episodic_memory']

    def add_memory(
            self,
            session_id: str,
            role: str,
            content: str,
            importance: float
    ):
        """
        添加记忆
        """
        self.working_memory.add_message(
            session_id=session_id,
            role=role,
            content=content,
            importance=importance
        )

        self.episodic_memory.add_episode(
            session_id=session_id,
            role=role,
            content=content,
            importance=importance
        )

    def search(
            self,
            query: str,
            limit: int,
            session_id: str = "default"
    ) -> List[Tuple[float, Dict[str, str]]]:
        """
        搜索记忆 - 动态自适应混合检索
        """
        candidate_limit = limit * 2

        working_raw = self.working_memory.retrieve(
            session_id=session_id,
            query=query,
            limit=candidate_limit
        )
        valid_working = [
            item for item in working_raw
            if item[1].get("role") != "error"
        ]

        episodic_raw = self.episodic_memory.retrieve(
            query=query,
            limit=candidate_limit,
            session_id=session_id
        )

        scored: List[Tuple[float, Dict[str, str]]] = []

        if valid_working:
            raw_scores = [s for s, _ in valid_working]
            max_w = max(raw_scores)
            if max_w > 0:
                for score, item_dict in valid_working:
                    norm = score / max_w
                    scored.append((norm, item_dict))

        if episodic_raw:
            raw_scores = [s for s, _ in episodic_raw]
            max_e = max(raw_scores)
            if max_e > 0:
                for score_float, item in episodic_raw:
                    norm = (score_float / max_e) * 0.95
                    scored.append((
                        norm,
                        {"role": item.role, "content": item.content, "time": item.get_timestamp().strftime("%H:%M")}
                    ))

        scored.sort(key=lambda x: x[0], reverse=True)

        # 去重: 相同 (role, content) 只保留评分最高的
        seen = set()
        deduped = []
        for score, item_dict in scored:
            key = (item_dict.get("role", ""), item_dict.get("content", ""))
            if key not in seen:
                seen.add(key)
                deduped.append((score, item_dict))
        scored = deduped

        result = []
        for score, item_dict in scored[:limit]:
            int_score = min(100, max(1, int(score * 100)))
            result.append((int_score, item_dict))

        return result
