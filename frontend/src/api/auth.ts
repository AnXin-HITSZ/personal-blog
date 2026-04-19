import request from '@/utils/request'
import type { Result, LoginDTO, RegisterDTO, UserInfo } from '@/types/api'

// 🔥 修复：必须用 async/await 取出 response.data，否则拿不到后端数据
export const loginApi = async (data: LoginDTO): Promise<Result> => {
  // request 返回的是 Axios 响应对象，必须取 .data 才是后端的 Result
  const res = await request.post('/user/account/login', data)
  return res.data as Result
}

export const registerApi = async (data: RegisterDTO): Promise<Result> => {
  const res = await request.post('/user/account/register', data)
  return res.data as Result
}

export const getUserInfoApi = async (): Promise<Result<UserInfo>> => {
  const res = await request.get('/user/account/info')
  return res.data as Result<UserInfo>
}