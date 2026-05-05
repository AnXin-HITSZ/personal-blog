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
  isAdmin: number
}

export interface RAGKnowledgeBase {
  ragId?: number
  userId?: number
  name: string
  description?: string
  namespace: string
  collectionName?: string
  filePath?: string
  fileCount?: number
  status?: number
  createdAt?: string
  updatedAt?: string
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
  timestamp?: number
}

export interface ChatRequest {
  sessionId: string
  messages: ChatMessage[]
  userId?: number
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

export interface MemoryItem {
  timestamp: string
  role: string
  content: string
}

export interface ReActData {
  steps: ReActStep[]
  finalAnswer: string
}

export interface SessionDTO {
  sessionId: string
  title: string
  preview?: string
  createdAt: number
  updatedAt: number
  messageCount: number
}

// ---- Plan / Task types ----

export type TaskState = 'open' | 'in_progress' | 'completed' | 'verified' | 'abandoned'

export interface PlanTask {
  taskId?: number
  parentTaskId?: number
  taskPath: string
  taskGoal: string
  taskState: TaskState
  displayOrder: number
  subtasks: PlanTask[]
}

export interface Plan {
  planId?: number
  userId?: number
  sessionId?: string
  mainGoal: string
  rootTask?: PlanTask
  createdAt?: string
  updatedAt?: string
}

export interface PlanEvent {
  type: 'plan_init' | 'plan_task_added' | 'plan_task_update'
  data: Record<string, any>
}