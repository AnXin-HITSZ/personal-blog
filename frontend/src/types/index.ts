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
