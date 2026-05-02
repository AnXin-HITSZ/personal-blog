import request from '@/utils/request'
import type { Result, SessionDTO } from '@/types/api'

/**
 * 获取当前用户的所有历史会话
 */
export const listSessionsApi = async (): Promise<SessionDTO[]> => {
  const res = await request.get('/api/history/list')
  const body = res.data as Result<SessionDTO[]>
  if (body.success && body.data) {
    return body.data
  }
  throw new Error(body.errorMsg || '获取历史会话失败')
}

/**
 * 获取指定会话的消息内容
 */
export const getSessionMessagesApi = async (sessionId: string): Promise<any[]> => {
  const res = await request.get(`/api/history/${sessionId}`)
  const body = res.data as Result<any[]>
  if (body.success && body.data) {
    return body.data
  }
  throw new Error(body.errorMsg || '获取会话消息失败')
}

/**
 * 删除指定会话
 */
export const deleteSessionApi = async (sessionId: string): Promise<void> => {
  const res = await request.delete(`/api/history/${sessionId}`)
  const body = res.data as Result
  if (!body.success) {
    throw new Error(body.errorMsg || '删除会话失败')
  }
}

/**
 * 更新会话标题
 */
export const updateSessionTitleApi = async (sessionId: string, title: string): Promise<void> => {
  const res = await request.put(`/api/history/${sessionId}/title`, { title })
  const body = res.data as Result
  if (!body.success) {
    throw new Error(body.errorMsg || '更新标题失败')
  }
}
