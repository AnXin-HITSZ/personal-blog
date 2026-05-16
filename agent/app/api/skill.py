"""Skill 管理接口

提供 Agent 能力的可视化管理和热插拔：
- GET /skills — 列出所有 Skill 及当前启用状态
- POST /skills/configure — 保存用户偏好并重新初始化 Agent
"""

from typing import List

from fastapi import APIRouter
from pydantic import BaseModel
from loguru import logger

from app.core.skill_registry import skill_registry
from app.services.rag_agent_service import rag_agent_service

router = APIRouter()


class ConfigureSkillsRequest(BaseModel):
    """Skill 配置请求"""
    enabled_skills: List[str]


@router.get("/skills")
async def list_skills():
    """列出所有可注册的 Skill 及其启用状态"""
    try:
        all_skills = skill_registry.list_skills()
        current_enabled = rag_agent_service.enabled_skills

        # 如果未自定义，回退到 config 默认值
        if current_enabled is None:
            from app.config import config
            current_enabled = [
                s.strip() for s in config.default_enabled_skills.split(",") if s.strip()
            ]

        return {
            "code": 200,
            "message": "success",
            "data": {
                "skills": all_skills,
                "enabled": current_enabled,
            },
        }
    except Exception as e:
        logger.error(f"获取 Skill 列表失败: {e}")
        return {
            "code": 500,
            "message": str(e),
            "data": None,
        }


@router.post("/skills/configure")
async def configure_skills(request: ConfigureSkillsRequest):
    """用户自定义启用/禁用 Skill

    1. 校验所有 Skill 名称有效
    2. 持久化到 Redis
    3. 立即重新初始化 Agent，后续对话生效
    """
    try:
        # 1. 校验请求的 skill 名称都有效
        invalid = []
        for name in request.enabled_skills:
            if not skill_registry.get_skill(name):
                invalid.append(name)

        if invalid:
            return {
                "code": 400,
                "message": f"Skill 不存在: {', '.join(invalid)}",
                "data": None,
            }

        # 2. 持久化用户偏好（写入 Redis，供跨会话使用）
        from app.core.redis_client import redis_manager
        redis = await redis_manager.connect()
        await redis.set("user_skills:default", ",".join(request.enabled_skills))

        # 3. 重新初始化 Agent（热插拔，不影响当前进行中的对话）
        await rag_agent_service.reinitialize(request.enabled_skills)

        logger.info(f"Skill 配置已更新: {request.enabled_skills}")

        return {
            "code": 200,
            "message": "Skill 配置已更新，将在下一轮对话生效",
            "data": {"enabled": request.enabled_skills},
        }
    except Exception as e:
        logger.error(f"配置 Skill 失败: {e}")
        return {
            "code": 500,
            "message": str(e),
            "data": None,
        }
