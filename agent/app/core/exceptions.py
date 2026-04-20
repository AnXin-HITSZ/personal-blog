class AgentsException(Exception):
    """
    Agents 基础异常类
    """
    pass

class LLMException(AgentsException):
    """
    LLM 相关异常
    """
    pass

class AgentException(AgentsException):
    """
    Agent 相关异常
    """
    pass

class ConfigException(AgentsException):
    """
    配置相关异常
    """
    pass

class ToolException(AgentsException):
    """
    工具相关异常
    """
    pass
