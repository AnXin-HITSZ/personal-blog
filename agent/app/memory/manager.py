from typing import List, Dict, Tuple
from datetime import datetime

import app.memory.working_memory as working_memory
import app.memory.episodic_memory as episodic_memory
from app.memory import WorkingMemory
from app.memory import EpisodicMemory


class UnifiedMemoryManager:
    """
    统一记忆管理器: 整合四种记忆类型
    """

    def __init__(
            self,
            working_memory_config: working_memory.MemoryConfig,
            episodic_memory_config: episodic_memory.MemoryConfig
    ):
        self.working_memory_config = working_memory_config
        self.episodic_memory_config = episodic_memory_config

        self.memory_types = {}
        self.memory_types['working_memory'] = WorkingMemory(self.working_memory_config)
        self.memory_types['episodic_memory'] = EpisodicMemory(self.episodic_memory_config)
