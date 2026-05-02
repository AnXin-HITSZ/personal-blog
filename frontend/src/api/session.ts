import request from '@/utils/request'
import type { Result } from '@/types/api'

/**
 * 从后端获取新的对话 sessionId
 */
export const initSessionApi = async (): Promise<string> => {
  const res = await request.post('/api/session/init')
  const body = res.data as Result<{ sessionId: string }>
  if (body.success && body.data) {
    return body.data.sessionId
  }
  throw new Error(body.errorMsg || '获取 session 失败')
}

/**
 * 清除当前对话 session，返回新的 sessionId
 */
export const clearSessionApi = async (): Promise<string> => {
  const res = await request.post('/api/session/clear')
  const body = res.data as Result<{ sessionId: string }>
  if (body.success && body.data) {
    return body.data.sessionId
  }
  throw new Error(body.errorMsg || '清除 session 失败')
}
