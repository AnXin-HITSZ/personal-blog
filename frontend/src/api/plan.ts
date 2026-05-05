import request from '@/utils/request'
import type { Result, Plan } from '@/types/api'

/**
 * 根据会话 ID 获取计划
 */
export function getPlanBySessionApi(sessionId: string): Promise<Result<Plan>> {
  return request.get(`/api/plan/${sessionId}`)
}

/**
 * 删除计划
 */
export function deletePlanApi(planId: number): Promise<Result<null>> {
  return request.delete(`/api/plan/${planId}`)
}
