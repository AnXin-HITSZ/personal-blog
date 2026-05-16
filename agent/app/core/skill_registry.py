"""Skill 注册中心

Skill = 可命名的、自描述的能力包，包含：
- Tools: Agent 可调用的函数集合
- System Prompt Fragment: 指导 LLM 如何使用该 Skill 的行为描述
- 元数据: name, description, enabled_by_default

提供全局注册中心，支持动态注册/注销/查询。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from langchain_core.tools import BaseTool
from loguru import logger


@dataclass
class Skill:
    """Skill 定义

    Attributes:
        name: 唯一标识符，如 "rag"
        description: 人类可读的描述，如 "基于 RAG 的知识库检索"
        tools: 归属于该 Skill 的工具列表
        system_prompt_fragment: 注入 System Prompt 的指导文本
        enabled_by_default: 默认是否启用
    """
    name: str
    description: str
    tools: List[BaseTool] = field(default_factory=list)
    system_prompt_fragment: str = ""
    enabled_by_default: bool = True


class SkillRegistry:
    """全局 Skill 注册中心"""

    def __init__(self):
        self._skills: Dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        """注册 Skill

        同名 Skill 后注册覆盖前者（方便热更新）。

        Args:
            skill: Skill 实例
        """
        self._skills[skill.name] = skill
        logger.info(f"Skill 已注册: {skill.name} ({len(skill.tools)} 个工具)")

    def unregister(self, name: str) -> None:
        """注销 Skill

        Args:
            name: Skill 名称
        """
        if name in self._skills:
            del self._skills[name]
            logger.info(f"Skill 已注销: {name}")

    def get_skill(self, name: str) -> Optional[Skill]:
        """按名称获取 Skill

        Args:
            name: Skill 名称

        Returns:
            Optional[Skill]: Skill 实例，不存在则返回 None
        """
        return self._skills.get(name)

    def get_enabled_tools(self, enabled_skills: List[str]) -> List[BaseTool]:
        """获取指定 Skill 列表中的所有工具（扁平化聚合）

        Args:
            enabled_skills: 启用的 Skill 名称列表

        Returns:
            List[BaseTool]: 聚合后的工具列表
        """
        tools: List[BaseTool] = []
        seen_names: set = set()

        for skill_name in enabled_skills:
            skill = self._skills.get(skill_name)
            if not skill:
                logger.warning(f"Skill '{skill_name}' 不存在，跳过")
                continue

            for tool in skill.tools:
                # 去重（防止同一工具被多个 Skill 注册）
                tool_name = tool.name if hasattr(tool, "name") else str(tool)
                if tool_name not in seen_names:
                    seen_names.add(tool_name)
                    tools.append(tool)

        return tools

    def get_system_prompt_extensions(self, enabled_skills: List[str]) -> str:
        """聚合启用 Skill 的 system_prompt_fragment

        Args:
            enabled_skills: 启用的 Skill 名称列表

        Returns:
            str: 拼接后的扩展文本，按换行分隔
        """
        fragments: List[str] = []

        for skill_name in enabled_skills:
            skill = self._skills.get(skill_name)
            if skill and skill.system_prompt_fragment:
                fragments.append(skill.system_prompt_fragment)

        return "\n\n".join(fragments)

    def list_skills(self) -> List[Dict]:
        """列出所有注册的 Skill 元信息

        Returns:
            List[Dict]: [{name, description, tool_count, enabled_by_default}, ...]
        """
        return [
            {
                "name": skill.name,
                "description": skill.description,
                "tool_count": len(skill.tools),
                "enabled_by_default": skill.enabled_by_default,
            }
            for skill in self._skills.values()
        ]

    def register_default_skills(self) -> None:
        """注册内置默认 Skill"""
        from app.tools import retrieve_knowledge, get_current_time

        self.register(Skill(
            name="rag",
            description="基于 RAG 知识库检索博客内容回答技术问题",
            tools=[retrieve_knowledge],
            system_prompt_fragment=(
                "你拥有一个 RAG 知识库，其中存储了博客文章和技术文档。"
                "当用户询问技术问题、博客内容或需要参考资料时，"
                "应使用 retrieve_knowledge 工具检索相关知识后再回答。"
            ),
        ))

        self.register(Skill(
            name="time",
            description="获取当前日期和时间",
            tools=[get_current_time],
            enabled_by_default=True,
            system_prompt_fragment=(
                "你可以获取当前的日期和时间信息（北京时间，UTC+8）。"
                "当用户询问「现在几点」「今天星期几」「今天日期」等时间相关问题时，"
                "应使用 get_current_time 工具获取当前时间后再回答。"
            ),
        ))

        self.register(Skill(
            name="mcp",
            description="外部 MCP 服务集成，提供监控告警和系统指标等信息",
            tools=[],  # 工具在初始化时动态填充
            system_prompt_fragment=(
                "你可以调用外部 MCP 服务来获取监控告警、系统指标等信息。"
                "MCP 工具会自动可用。"
            ),
        ))

        logger.info(f"已注册 {len(self._skills)} 个默认 Skill")


# 全局单例
skill_registry = SkillRegistry()
