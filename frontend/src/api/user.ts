import request from './request'
import type { ApiResult, LoginForm, RegisterForm, UserInfo } from '@/types'

export function loginApi(data: LoginForm): Promise<ApiResult<string>> {
  return request.post('/user/account/login', data).then((r) => r.data)
}

export function registerApi(data: RegisterForm): Promise<ApiResult<null>> {
  return request.post('/user/account/register', data).then((r) => r.data)
}

export function getUserInfoApi(): Promise<ApiResult<UserInfo>> {
  return request.get('/user/account/info').then((r) => r.data)
}
