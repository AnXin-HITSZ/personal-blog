import type { ChatRequest, ChatResponse } from '@/types/api'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

/**
 * 流式聊天，使用 Server-Sent Events (SSE)
 * @param request 聊天请求
 * @param onMessage 收到每个消息块时的回调
 * @param onError 错误回调
 * @param onComplete 完成回调
 * @returns 一个函数，用于中止请求
 */
export const streamChat = (
  request: ChatRequest,
  onMessage: (chunk: string) => void,
  onError?: (error: any) => void,
  onComplete?: () => void
): (() => void) => {
  const abortController = new AbortController()
  const token = localStorage.getItem('token')
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  // 确保开启流式
  const payload: ChatRequest = {
    ...request,
    isStream: true,
  }

  fetch(`${API_BASE}/api/agent/chat`, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
    signal: abortController.signal,
  })
    .then(async (response) => {
      console.log('SSE connected, status:', response.status, 'content-type:', response.headers.get('content-type'))
      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('Response body is not readable')
      }

      const decoder = new TextDecoder()
      let buffer = ''

      try {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || '' // 保留未完成的行

          for (const line of lines) {
            if (line.startsWith('data:')) {
              const data = line.slice(5).trim()
              if (data === '[DONE]') {
                onComplete?.()
                return
              }
              if (data === '') continue
              try {
                const parsed = JSON.parse(data)
                console.log('Parsed SSE chunk:', parsed)
                // 如果解析后的对象有content字段，使用它；否则使用原始data
                const content = parsed.content ?? data
                onMessage(content)
              } catch (e) {
                console.log('SSE raw data (not JSON):', data)
                // 不是JSON，直接使用原始数据
                onMessage(data)
              }
            }
          }
        }
      } finally {
        reader.releaseLock()
      }
      onComplete?.()
    })
    .catch((error) => {
      if (error.name === 'AbortError') {
        // 主动中止，不触发错误回调
        return
      }
      console.error('Stream chat error:', error)
      onError?.(error)
    })

  return () => abortController.abort()
}

/**
 * 非流式聊天（一次性返回完整响应）
 * @param request 聊天请求
 * @returns 完整的聊天响应
 */
export const chat = async (request: ChatRequest): Promise<ChatResponse> => {
  const token = localStorage.getItem('token')
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const payload: ChatRequest = {
    ...request,
    isStream: false,
  }

  const response = await fetch(`${API_BASE}/api/agent/chat`, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    throw new Error(`HTTP error ${response.status}`)
  }

  // 非流式响应直接返回JSON
  return await response.json() as ChatResponse
}