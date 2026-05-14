import request from './request'
import type { AgentResult, ApiResult, KnowledgeBaseFile, ChatMessage, SessionSummary } from '@/types'

const BASE = '/api/agent'

/** 非流式对话 */
export async function chatApi(
  question: string,
  sessionId: string,
): Promise<AgentResult> {
  return request
    .post(`${BASE}/chat`, { question, sessionId })
    .then((r) => r.data)
}

/** 清空会话 */
export async function clearSessionApi(sessionId: string): Promise<any> {
  return request
    .post(`${BASE}/chat/clear`, { sessionId })
    .then((r) => r.data)
}

/** 获取会话信息 */
export async function getSessionApi(sessionId: string): Promise<any> {
  return request.get(`${BASE}/chat/session/${sessionId}`).then((r) => r.data)
}

/** 获取会话历史消息（从 Redis 持久化存储读取） */
export async function fetchHistoryApi(sessionId: string): Promise<ApiResult<{
  session_id: string
  message_count: number
  history: ChatMessage[]
}>> {
  return request.get(`${BASE}/chat/session/${sessionId}`).then((r) => r.data)
}

/** 获取所有会话列表 */
export async function listSessionsApi(): Promise<ApiResult<SessionSummary[]>> {
  return request.get(`${BASE}/chat/sessions`).then((r) => r.data)
}

/** 删除指定会话 */
export async function deleteSessionApi(sessionId: string): Promise<ApiResult> {
  return request.delete(`${BASE}/chat/session/${sessionId}`).then((r) => r.data)
}

/** 上传文件到知识库 */
export async function uploadFileApi(file: File): Promise<ApiResult> {
  const formData = new FormData()
  formData.append('file', file)
  return request
    .post(`${BASE}/upload`, formData, {
      // 不手设置 Content-Type，让 axios 自动添加 multipart boundary
      timeout: 120000,
    })
    .then((r) => r.data)
}

/** 知识库文件列表 */
export async function listFilesApi(ext?: string): Promise<ApiResult<KnowledgeBaseFile[]>> {
  const params = ext ? { ext } : {}
  return request.get(`${BASE}/files`, { params }).then((r) => r.data)
}

/** 索引知识库目录 */
export async function indexDirectoryApi(directoryPath?: string): Promise<ApiResult> {
  return request
    .post(`${BASE}/index_directory`, { directory_path: directoryPath })
    .then((r) => r.data)
}

/** 删除知识库中的文件索引 */
export async function deleteSourceApi(filePath: string): Promise<ApiResult> {
  return request
    .delete(`${BASE}/rag/source`, { params: { file_path: filePath } })
    .then((r) => r.data)
}

/** 获取知识库统计 */
export async function getRagStatsApi(): Promise<ApiResult> {
  return request.get(`${BASE}/rag/stats`).then((r) => r.data)
}

/**
 * 流式对话 — 使用 fetch 读取 SSE 事件流
 *
 * 返回一个 AsyncGenerator，每次 yield { type, data }
 * 事件类型: content, tool_call, search_results, done, error
 */
export async function* streamChatApi(
  question: string,
  sessionId: string,
): AsyncGenerator<{ type: string; data: any }> {
  const token = localStorage.getItem('token')

  const response = await fetch(`${BASE}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ question, sessionId }),
  })

  if (!response.ok) {
    throw new Error(`SSE 请求失败: ${response.status}`)
  }

  const reader = response.body?.getReader()
  if (!reader) {
    throw new Error('浏览器不支持 ReadableStream')
  }

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      // SSE 标准：data: 后面可带空格也可不带（Spring Boot SseEmitter 不带空格）
      if (line.startsWith('data:')) {
        const jsonStr = line.substring(5).trim()
        if (!jsonStr) continue
        try {
          const parsed = JSON.parse(jsonStr)
          yield parsed
        } catch {
          // ignore malformed JSON
        }
      }
    }
  }
}
