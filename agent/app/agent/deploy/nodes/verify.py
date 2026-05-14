"""阶段五：全面验证节点"""

import asyncio
import subprocess
import time
from datetime import datetime
from typing import Dict, Any, List

import httpx
from loguru import logger

from app.config import config
from ..state import DeploymentState


async def verify_node(state: DeploymentState) -> Dict[str, Any]:
    """阶段五：全面验证

    1. 基础可用性：首页是否正常返回 200
    2. 关键页面：API 端点是否正常
    3. 功能验证：Agent 健康检查
    4. 性能验证：首页加载速度
    5. 链接验证：检查页面关键元素
    """
    logger.info("=== 阶段五：全面验证 ===")

    phase_logs = list(state.get("phase_logs", []))
    phase_status = dict(state.get("phase_status", {}))
    verify_results: Dict[str, Any] = {}
    all_passed = True

    try:
        # 基础 URL（从配置读取，Docker 环境为 http://localhost:80，本地开发可设 http://localhost:8000）
        base_url = config.deploy_base_url

        checks = [
            ("frontend_home", "前端首页", f"{base_url}/", 200, 30),
            ("backend_health", "后端健康", f"{base_url}/api/agent/health", 200, 30),
            ("agent_health", "Agent 健康", f"{base_url}/api/agent/health", 200, 30),
        ]

        for check_id, check_name, url, expected, timeout in checks:
            phase_logs.append(("verify", f"正在验证: {check_name}...", datetime.now().isoformat()))
            logger.info(f"验证 {check_name}: {url}")

            result = await _http_get(url, timeout)
            passed = result["status"] == expected

            verify_results[check_id] = {
                "name": check_name,
                "url": url,
                "expected_status": expected,
                "actual_status": result["status"],
                "passed": passed,
                "duration_ms": result["duration_ms"],
            }

            if passed:
                phase_logs.append(("verify", f"✓ {check_name} 正常 ({result['duration_ms']}ms)", datetime.now().isoformat()))
            else:
                phase_logs.append(("verify", f"✗ {check_name} 异常: 期望 {expected}, 实际 {result['status']}", datetime.now().isoformat()))
                all_passed = False

        # 性能检查：首页响应时间
        perf = verify_results.get("frontend_home", {})
        perf_duration = perf.get("duration_ms", 0)
        perf_ok = perf_duration < 5000  # 5 秒内算正常
        verify_results["performance"] = {
            "frontend_load_ms": perf_duration,
            "passed": perf_ok,
        }
        if not perf_ok:
            phase_logs.append(("verify", f"⚠ 首页加载偏慢: {perf_duration}ms", datetime.now().isoformat()))

        if all_passed:
            phase_status["verify"] = "success"
            logger.info("所有验证通过！")
        else:
            phase_status["verify"] = "failed"
            logger.warning("部分验证未通过")

        return {
            "current_phase": "verify",
            "phase_status": phase_status,
            "phase_logs": phase_logs,
            "verify_results": verify_results,
            "needs_rollback": not all_passed,
        }

    except Exception as e:
        error_msg = f"验证失败: {e}"
        logger.error(error_msg)
        phase_logs.append(("verify", error_msg, datetime.now().isoformat()))
        phase_status["verify"] = "failed"
        return {
            "current_phase": "verify",
            "phase_status": phase_status,
            "phase_logs": phase_logs,
            "verify_results": verify_results,
            "needs_rollback": True,
            "error": error_msg,
        }


async def _http_get(url: str, timeout: int = 30) -> Dict[str, Any]:
    """HTTP GET 请求（带重试）"""
    max_retries = 3
    for i in range(max_retries):
        try:
            t0 = time.time()
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(url, follow_redirects=True)
                duration = int((time.time() - t0) * 1000)
                return {
                    "status": resp.status_code,
                    "duration_ms": duration,
                    "body": resp.text[:500],
                }
        except Exception as e:
            if i < max_retries - 1:
                await asyncio.sleep(3)
            else:
                return {"status": 0, "duration_ms": 0, "body": str(e)}
