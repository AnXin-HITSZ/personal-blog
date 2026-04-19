// src/utils/request.ts
import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 10000,
  withCredentials: true
})

// 请求拦截器（带调试日志，核心排查）
request.interceptors.request.use(
  (config) => {
    // 🔥 调试1：打印本地存储的Token
    const token = localStorage.getItem('token')
    console.log('【前端】本地Token：', token)

    // 🔥 调试2：强制写入请求头（防止丢失）
    if (token) {
      config.headers['Authorization'] = 'Bearer ' + token
      console.log('【前端】请求头已设置：', config.headers['Authorization'])
    }

    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器（无TS报错）
request.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      ElMessage.error('登录已过期')
      window.location.href = '/login'
    }
    ElMessage.error('请求失败')
    return Promise.reject(error)
  }
)

export default request