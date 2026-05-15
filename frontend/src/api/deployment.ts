import request from './request'
import type { ApiResult, DeploymentSummary, DeploymentDetail } from '@/types'

const BASE = '/api/agent/deploy'

/** 手动触发部署 */
export async function triggerDeployApi(branch?: string): Promise<ApiResult<{ deployment_id: string }>> {
  return request.post(`${BASE}/trigger`, { branch }).then((r) => r.data)
}

/** 获取部署历史 */
export async function getDeployHistoryApi(
  page = 1,
  size = 20,
): Promise<ApiResult<{ deployments: DeploymentSummary[]; total: number; page: number }>> {
  return request.get(`${BASE}/history`, { params: { page, size } }).then((r) => r.data)
}

/** 获取部署详情（轮询用） */
export async function getDeployDetailApi(id: string): Promise<ApiResult<DeploymentDetail>> {
  return request.get(`${BASE}/${id}`).then((r) => r.data)
}

/** 取消部署 */
export async function cancelDeployApi(id: string): Promise<ApiResult> {
  return request.post(`${BASE}/${id}/cancel`).then((r) => r.data)
}

/** 获取 Agent 变更 diff（审批前审查用） */
export async function getDeployDiffApi(id: string): Promise<ApiResult<{ diff: string }>> {
  return request.get(`${BASE}/${id}/diff`).then((r) => r.data)
}

/** 审批通过 Agent 变更，继续部署 */
export async function approveDeployApi(id: string): Promise<ApiResult> {
  return request.post(`${BASE}/${id}/approve`).then((r) => r.data)
}
