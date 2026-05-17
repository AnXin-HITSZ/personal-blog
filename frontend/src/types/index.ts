/** 统一后端响应格式 */
export interface ApiResult<T = any> {
  success: boolean
  errorMsg: string | null
  data: T
  total: number | null
}

export interface UserInfo {
  userId: number
  username: string
  isAdmin: number
}

export interface Article {
  articleId?: number
  userId?: number
  title: string
  content: string
  createTime?: string
  updateTime?: string
}

export interface LoginForm {
  username: string
  password: string
}

export interface RegisterForm {
  username: string
  password: string
  confirmedPassword: string
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp?: string
  toolCalls?: ToolCallEvent[]
}

export interface ChatResponse {
  success: boolean
  answer: string
  errorMessage: string | null
}

export interface KnowledgeBaseFile {
  filename: string
  file_path: string
  size: number
  last_modified: string
}

export interface AgentResult {
  code: number
  message: string
  data: ChatResponse
}

export interface ToolCallEvent {
  name: string
  status: 'start' | 'end'
  result?: string
}

/** ─── 部署相关类型 ─── */

export interface DeploymentSummary {
  deployment_id: string
  trigger_type: 'webhook' | 'manual'
  target_branch: string
  commit_hash: string
  commit_message: string
  final_status: 'running' | 'success' | 'failed' | 'rolled_back' | 'cancelled'
  current_phase: string
  created_at: string
  updated_at: string
  duration_ms: number
}

export interface PhaseInfo {
  name: string
  label: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'skipped'
}

export interface LogEntry {
  phase: string
  message: string
  timestamp: string
}

export interface DeploymentDetail {
  deployment_id: string
  trigger_type: string
  target_branch: string
  commit_hash: string
  previous_commit_hash: string
  commit_message: string
  final_status: string
  current_phase: string
  phases: PhaseInfo[]
  build_results: Record<string, any>
  verify_results: Record<string, any>
  logs: LogEntry[]
  error: string
  created_at: string
  updated_at: string
  duration_ms: number
}

/** 会话摘要（用于历史列表） */
export interface SessionSummary {
  session_id: string
  title: string
  message_count: number
  created_at: string
  updated_at: string
}

/** ─── Agent CI/CD 新增类型 ─── */

/** Agent 思考/诊断事件 */
export interface AgentThought {
  content: string
  phase: string
  plan?: string[]
  detail?: string
}

/** Agent 修复尝试记录 */
export interface FixAttempt {
  attempt: number
  max_retries: number
  target?: string
  diff?: string
  phase: string
}

/** 扩展的部署详情（含 Agent 字段） */
export interface AgentDeploymentDetail extends DeploymentDetail {
  agent_thoughts?: AgentThought[]
  fix_attempts?: FixAttempt[]
  needs_approval?: boolean
  approval_granted?: boolean
  pending_diff?: string
  response?: string
  report?: string
}
