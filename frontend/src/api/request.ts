import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const request = axios.create({
  baseURL: '/',
  timeout: 30000,
})

/** 无需携带 Token 的路径 */
const NO_AUTH_PATHS = ['/user/account/login', '/user/account/register']

request.interceptors.request.use((config) => {
  const url = config.url ?? ''
  if (!NO_AUTH_PATHS.some((p) => url.startsWith(p))) {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
  }
  return config
})

request.interceptors.response.use(
  (res) => res,
  (err) => {
    const url = err.config?.url ?? ''
    const isAuthPath = ['/user/account/login', '/user/account/register'].some((p) =>
      url.startsWith(p),
    )
    const isAgentPath = url.startsWith('/api/agent/')

    // 仅对用户认证接口的 401/403 做登出重定向
    // Agent 接口的 401 可能是代理链路问题，不应注销用户
    if (!isAuthPath && !isAgentPath && (err.response?.status === 401 || err.response?.status === 403)) {
      localStorage.removeItem('token')
      ElMessage.error({ message: '登录已过期，请重新登录', duration: 2000 })
      router.push('/login')
    } else {
      ElMessage.error({ message: err.response?.data?.errorMsg || err.message || '请求失败', duration: 2000 })
    }
    return Promise.reject(err)
  },
)

export default request
