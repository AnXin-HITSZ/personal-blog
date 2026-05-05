<template>
  <router-view />
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

onMounted(() => {
  // Token 存在但用户信息未加载 → 从后端获取
  if (authStore.token && !authStore.userInfo) {
    authStore.getUserInfo().catch(() => {
      // token 无效，getUserInfo 已自动清除
    })
  }
})
</script>

<style scoped>
#app {
  min-height: 100vh;
}
</style>