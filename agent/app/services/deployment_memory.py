"""部署记忆服务 — Redis 持久化部署状态与历史

Redis 键方案：
  deploy:{id}:state   HASH  — 部署状态快照
  deploy:{id}:logs    LIST  — 日志条目 (JSON)
  deploy:history      ZSET  — 部署 ID 按时间排序
"""

import json
from datetime import datetime
from typing import List, Optional, Dict, Any

from loguru import logger
from redis.asyncio import Redis as AsyncRedis

from app.core.redis_client import redis_manager

DEPLOY_PREFIX = "deploy"


def _state_key(deploy_id: str) -> str:
    return f"{DEPLOY_PREFIX}:{deploy_id}:state"


def _logs_key(deploy_id: str) -> str:
    return f"{DEPLOY_PREFIX}:{deploy_id}:logs"


def _history_key() -> str:
    return f"{DEPLOY_PREFIX}:history"


class DeploymentMemory:
    """部署记忆服务 — Redis 持久化存储"""

    def __init__(self):
        self._redis: Optional[AsyncRedis] = None

    async def _get_redis(self) -> AsyncRedis:
        if self._redis is None:
            try:
                self._redis = await redis_manager.connect()
            except Exception as e:
                logger.error(f"部署记忆服务无法连接 Redis: {e}")
                raise
        return self._redis

    async def save_state(self, deploy_id: str, state: Dict[str, Any]):
        """保存部署状态到 Redis"""
        try:
            redis = await self._get_redis()

            # redis hset 只接受 string / bytes / int，复杂类型需序列化
            serializable = {}
            for k, v in state.items():
                if isinstance(v, bool):
                    serializable[k] = 1 if v else 0
                elif isinstance(v, (str, int, float)):
                    serializable[k] = v
                elif v is None:
                    serializable[k] = ""
                else:
                    try:
                        serializable[k] = json.dumps(v, ensure_ascii=False)
                    except (TypeError, OverflowError):
                        serializable[k] = str(v)

            await redis.hset(_state_key(deploy_id), mapping=serializable)

            # 更新历史 ZSET
            score = datetime.now().timestamp()
            await redis.zadd(_history_key(), {deploy_id: score})

        except Exception as e:
            logger.error(f"保存部署状态失败: {deploy_id}, 错误: {e}")

    async def get_state(self, deploy_id: str) -> Dict[str, Any]:
        """获取部署状态（自动反序列化 JSON 值）"""
        try:
            redis = await self._get_redis()
            raw = await redis.hgetall(_state_key(deploy_id))
            state = {}
            for k_bytes, v_bytes in raw.items():
                key = k_bytes.decode() if isinstance(k_bytes, bytes) else str(k_bytes)
                val = v_bytes.decode() if isinstance(v_bytes, bytes) else str(v_bytes)
                # 尝试反序列化 JSON
                try:
                    state[key] = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    state[key] = val
            return state
        except Exception as e:
            logger.error(f"获取部署状态失败: {deploy_id}, 错误: {e}")
            return {}

    async def append_log(self, deploy_id: str, phase: str, message: str):
        """追加部署日志"""
        try:
            redis = await self._get_redis()
            entry = json.dumps({
                "phase": phase,
                "message": message,
                "timestamp": datetime.now().isoformat(),
            }, ensure_ascii=False)
            await redis.rpush(_logs_key(deploy_id), entry)
        except Exception as e:
            logger.error(f"追加部署日志失败: {deploy_id}, 错误: {e}")

    async def get_logs(self, deploy_id: str) -> List[Dict[str, str]]:
        """获取部署日志"""
        try:
            redis = await self._get_redis()
            items = await redis.lrange(_logs_key(deploy_id), 0, -1)
            logs = []
            for item in items:
                try:
                    logs.append(json.loads(item))
                except json.JSONDecodeError:
                    continue
            return logs
        except Exception:
            return []

    async def list_history(
        self, page: int = 1, size: int = 20
    ) -> Dict[str, Any]:
        """获取部署历史列表"""
        try:
            redis = await self._get_redis()

            total = await redis.zcard(_history_key())

            start = (page - 1) * size
            end = start + size - 1

            ids = await redis.zrevrange(_history_key(), start, end)

            deployments = []
            for deploy_id in ids:
                deploy_id = deploy_id if isinstance(deploy_id, str) else deploy_id.decode()
                state = await self.get_state(deploy_id)
                deployments.append({
                    "deployment_id": deploy_id,
                    "trigger_type": state.get("trigger_type", ""),
                    "target_branch": state.get("target_branch", ""),
                    "commit_hash": state.get("commit_hash", ""),
                    "commit_message": state.get("commit_message", ""),
                    "final_status": state.get("final_status", "running"),
                    "current_phase": state.get("current_phase", ""),
                    "created_at": "",
                    "updated_at": "",
                    "duration_ms": 0,
                })

            return {
                "deployments": deployments,
                "total": total,
                "page": page,
            }

        except Exception as e:
            logger.error(f"获取部署历史失败: {e}")
            return {"deployments": [], "total": 0, "page": page}

    async def get_running_deployment(self) -> Optional[str]:
        """获取当前正在运行的部署 ID"""
        try:
            redis = await self._get_redis()
            ids = await redis.zrevrange(_history_key(), 0, 20)
            for deploy_id in ids:
                deploy_id = deploy_id if isinstance(deploy_id, str) else deploy_id.decode()
                state = await self.get_state(deploy_id)
                if state.get("final_status") == "running":
                    return deploy_id
            return None
        except Exception:
            return None

    async def set_cancelled(self, deploy_id: str):
        """标记部署为已取消"""
        try:
            redis = await self._get_redis()
            await redis.hset(_state_key(deploy_id), "final_status", "cancelled")
        except Exception as e:
            logger.error(f"取消部署失败: {deploy_id}, 错误: {e}")


# 全局单例
deployment_memory = DeploymentMemory()
