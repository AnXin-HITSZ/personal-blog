"""部署接口模块

提供 Agent 驱动的 CI/CD 部署接口，兼容原有前端轮询协议。
"""

import hashlib
import hmac
import json

from fastapi import APIRouter, HTTPException, Request
from sse_starlette.sse import EventSourceResponse
from loguru import logger

from app.config import config
from app.models.deployment import ManualTriggerRequest, WebhookPayload
from app.services.cicd_service import cicd_service
from app.services.deployment_memory import deployment_memory

router = APIRouter()


def _verify_github_signature(payload: bytes, signature_header: str) -> bool:
    """验证 GitHub Webhook HMAC-SHA256 签名"""
    if not config.deploy_webhook_secret:
        logger.warning("Webhook secret 未配置，跳过签名验证")
        return True
    secret = config.deploy_webhook_secret.encode()
    expected = "sha256=" + hmac.new(secret, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def _verify_gitee_token(token: str) -> bool:
    """验证 Gitee Webhook Token"""
    if not config.deploy_webhook_secret:
        return True
    return token == config.deploy_webhook_secret


@router.post("/deploy/webhook")
async def deploy_webhook(request: Request):
    """GitHub/Gitee Webhook 入口

    接收推送事件，自动触发 Agent 驱动的部署流程
    """
    body = await request.body()
    user_agent = request.headers.get("User-Agent", "")
    is_github = "GitHub-Hookshot" in user_agent
    is_gitee = "Gitee" in user_agent or "git-oschina" in user_agent

    # 签名验证
    if is_github:
        sig = request.headers.get("X-Hub-Signature-256", "")
        if not _verify_github_signature(body, sig):
            logger.warning("GitHub Webhook 签名验证失败")
            raise HTTPException(status_code=401, detail="签名验证失败")
        logger.info("GitHub Webhook 签名验证通过")
    elif is_gitee:
        token = request.headers.get("X-Gitee-Token", "")
        if not _verify_gitee_token(token):
            logger.warning("Gitee Webhook Token 验证失败")
            raise HTTPException(status_code=401, detail="Token 验证失败")
        logger.info("Gitee Webhook Token 验证通过")
    else:
        logger.info(f"收到 Webhook 请求 (User-Agent: {user_agent})")

    # 解析 payload
    try:
        payload = WebhookPayload(**json.loads(body))
    except Exception as e:
        logger.error(f"解析 Webhook payload 失败: {e}")
        raise HTTPException(status_code=400, detail=f"无效的 payload: {e}")

    # 检查是否为 ping 事件
    if request.headers.get("X-GitHub-Event") == "ping":
        logger.info("收到 GitHub ping 事件")
        return {"message": "pong"}

    # 只处理推送到 main/master 分支
    if not payload.is_push_to_main:
        logger.info(f"忽略非主干分支推送: {payload.ref}")
        return {"message": f"忽略分支: {payload.ref}"}

    # 检查是否已有部署运行中
    running = await deployment_memory.get_running_deployment()
    if running:
        logger.warning(f"已有部署运行中: {running}")
        return {"message": f"已有部署运行中: {running}", "deployment_id": running}

    # 后台启动 Agent 部署
    import asyncio

    async def run_deploy():
        async for event in cicd_service.execute(
            trigger_type="webhook",
            branch="main",
        ):
            if event.get("type") == "phase_update":
                logger.info(f"[Webhook Agent 部署] 阶段: {event.get('phase')} = {event.get('status')}")

    asyncio.create_task(run_deploy())
    logger.info("Webhook 触发的 Agent 部署已启动")

    return {
        "message": "Agent 部署已启动",
        "commit": payload.commit_hash,
        "branch": payload.ref,
    }


@router.post("/deploy/trigger")
async def deploy_manual(request: ManualTriggerRequest):
    """手动触发 Agent 驱动的部署"""
    branch = request.branch or config.deploy_default_branch

    # 检查是否已有部署运行中
    running = await deployment_memory.get_running_deployment()
    if running:
        raise HTTPException(status_code=409, detail=f"已有部署运行中: {running}")

    import asyncio
    from datetime import datetime
    import uuid

    deployment_id = f"deploy-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"

    async def run_deploy():
        async for event in cicd_service.execute(
            trigger_type="manual",
            branch=branch,
            deployment_id=deployment_id,
        ):
            if event.get("type") == "phase_update":
                logger.info(f"[手动 Agent 部署] 阶段: {event.get('phase')} = {event.get('status')}")

    asyncio.create_task(run_deploy())

    return {"message": "Agent 部署已启动", "branch": branch, "deployment_id": deployment_id}


@router.get("/deploy/history")
async def deploy_history(page: int = 1, size: int = 20):
    """获取部署历史"""
    try:
        result = await cicd_service.get_history(page, size)
        return {"code": 200, "message": "success", "data": result}
    except Exception as e:
        logger.error(f"获取部署历史失败: {e}")
        return {"code": 500, "message": str(e), "data": {"deployments": [], "total": 0, "page": page}}


@router.get("/deploy/{deployment_id}")
async def deploy_detail(deployment_id: str):
    """获取部署详情（兼容原前端轮询协议）"""
    try:
        state = await cicd_service.get_state(deployment_id)
        return {"code": 200, "message": "success", "data": state}
    except Exception as e:
        logger.error(f"获取部署详情失败: {e}")
        return {"code": 500, "message": str(e), "data": None}


@router.post("/deploy/{deployment_id}/cancel")
async def cancel_deploy(deployment_id: str):
    """取消部署"""
    try:
        await cicd_service.cancel(deployment_id)
        return {"code": 200, "message": "已取消", "data": None}
    except Exception as e:
        return {"code": 500, "message": str(e), "data": None}


@router.get("/deploy/{deployment_id}/diff")
async def deploy_diff(deployment_id: str):
    """获取 Agent 修改的代码 diff（用于审批前审查）"""
    try:
        state = await deployment_memory.get_state(deployment_id)
        pending_diff = state.get("pending_diff", "")
        return {"code": 200, "message": "success", "data": {"diff": pending_diff}}
    except Exception as e:
        return {"code": 500, "message": str(e), "data": None}


@router.post("/deploy/{deployment_id}/approve")
async def approve_deploy(deployment_id: str):
    """审批通过 Agent 的变更，继续部署"""
    try:
        # 标记审批通过（CICDState 在下一轮 replanner 中检查此字段）
        await deployment_memory.save_state(deployment_id, {"approval_granted": True})
        return {"code": 200, "message": "已批准", "data": None}
    except Exception as e:
        return {"code": 500, "message": str(e), "data": None}


@router.get("/deploy/{deployment_id}/stream")
async def deploy_stream(deployment_id: str):
    """部署流水线 SSE 事件流"""
    async def event_generator():
        try:
            async for event in cicd_service.execute(trigger_type="manual", branch="main"):
                yield {
                    "event": "message",
                    "data": json.dumps(event, ensure_ascii=False),
                }
        except Exception as e:
            logger.error(f"部署流错误: {e}")
            yield {
                "event": "message",
                "data": json.dumps({"type": "error", "message": str(e)}, ensure_ascii=False),
            }

    return EventSourceResponse(event_generator())
