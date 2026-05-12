import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserInfo } from '@/types'
import { getUserInfoApi } from '@/api/user'

export const useUserStore = defineStore('user', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const userInfo = ref<UserInfo | null>(null)

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => userInfo.value?.isAdmin === 1)
  const username = computed(() => userInfo.value?.username ?? '')

  function setToken(val: string) {
    token.value = val
    localStorage.setItem('token', val)
  }

  function clearToken() {
    token.value = null
    userInfo.value = null
    localStorage.removeItem('token')
  }

  async function fetchUserInfo() {
    if (!token.value) return
    try {
      const res = await getUserInfoApi()
      if (res.success) {
        userInfo.value = res.data
      } else {
        clearToken()
      }
    } catch {
      clearToken()
    }
  }

  function logout() {
    clearToken()
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    isAdmin,
    username,
    setToken,
    clearToken,
    fetchUserInfo,
    logout,
  }
})
