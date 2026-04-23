import type { ChatRequest } from '@/types/api'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

/**
 * SimpleAgent 流式聊天
 */
export const streamSimpleAgentChat = (
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

  fetch(`${API_BASE}/api/agent/chat/simple_agent/stream`, {
    method: 'POST',
    headers,
    body: JSON.stringify(request),
    signal: abortController.signal,
  })
    .then(async (response) => {
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
          buffer = lines.pop() || ''

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
                onMessage(parsed.content ?? data)
              } catch (_e) {
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
      if (error.name === 'AbortError') return
      console.error('SimpleAgent stream error:', error)
      onError?.(error)
    })

  return () => abortController.abort()
}

/**
 * ReActAgent 流式聊天
 * 发送结构化事件: step / thought / action / observation / final_answer
 */
export const streamReActAgentChat = (
  request: ChatRequest,
  onEvent: (event: { type: string; data: any }) => void,
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

  fetch(`${API_BASE}/api/agent/chat/react_agent/stream`, {
    method: 'POST',
    headers,
    body: JSON.stringify(request),
    signal: abortController.signal,
  })
    .then(async (response) => {
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
          buffer = lines.pop() || ''

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
                onEvent(parsed)
              } catch (_e) {
                console.warn('Failed to parse ReAct event:', data)
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
      if (error.name === 'AbortError') return
      console.error('ReActAgent stream error:', error)
      onError?.(error)
    })

  return () => abortController.abort()
}
