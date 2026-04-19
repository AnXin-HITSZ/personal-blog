import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { LoginDTO, RegisterDTO, UserInfo } from '@/types/api'
import { loginApi, registerApi, getUserInfoApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const userInfo = ref<UserInfo | null>(null)

  const setToken = (newToken: string) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
    console.log('✅ Token 存储成功：', newToken)
  }

  const clearToken = () => {
    token.value = null
    localStorage.removeItem('token')
  }

  // 登录（正确获取Token）
  const login = async (data: LoginDTO) => {
    try {
      const response = await loginApi(data)
      // 后端直接返回Token字符串，直接存储
      setToken(response.data as string)
      // 获取用户信息
      await getUserInfo()
      return response
    } catch (error: any) {
      throw new Error(error.message || 'Login failed')
    }
  }

  const register = async (data: RegisterDTO) => {
    try {
      return await registerApi(data)
    } catch (error: any) {
      throw new Error(error.message || 'Registration failed')
    }
  }

  const getUserInfo = async () => {
    try {
      const response = await getUserInfoApi()
      userInfo.value = response.data as UserInfo
      return response
    } catch (error: any) {
      clearToken()
      throw error
    }
  }

  const logout = () => {
    clearToken()
    userInfo.value = null
  }

  return {
    token,
    userInfo,
    login,
    register,
    getUserInfo,
    logout
  }
})