from dataclasses import dataclass

@dataclass
class MemoryConfig:
    """
    工作记忆的配置类
    """
    memory_capacity: int = 50
    ttl_minutes: int = 120
    default_importance: float = 0.5
