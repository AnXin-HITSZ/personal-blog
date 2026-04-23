export interface Result<T = any> {
  success: boolean
  errorMsg?: string
  data?: T
  total?: number
}

export interface LoginDTO {
  username: string
  password: string
}

export interface RegisterDTO {
  username: string
  password: string
  confirmedPassword: string
}

export interface UserInfo {
  userId: number
  username: string
}

export interface Article {
  articleId?: number
  userId?: number
  title: string
  content: string
  createTime?: string
  updateTime?: string
}

export interface ChatMessage {
  role: string
  content: string
}

export interface ChatRequest {
  sessionId: string
  messages: ChatMessage[]
}

export interface ChatResponse {
  content: string
  model?: string
  usage?: Record<string, any>
}

export type AgentType = 'simple' | 'react'

export interface ReActStep {
  stepNumber: number
  thought?: string
  action?: { tool: string; input: string }
  observation?: string
  error?: string
}

export interface ReActData {
  steps: ReActStep[]
  finalAnswer: string
}