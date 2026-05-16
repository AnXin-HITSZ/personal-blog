<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { loginApi } from '@/api/user'
import type { LoginForm } from '@/types'
import { ElMessage } from 'element-plus'

const router = useRouter()
const store = useUserStore()

const form = reactive<LoginForm>({
  username: '',
  password: '',
})
const loading = ref(false)

async function handleLogin() {
  if (!form.username.trim()) {
    ElMessage.warning('请输入用户名')
    return
  }
  if (!form.password) {
    ElMessage.warning('请输入密码')
    return
  }

  loading.value = true
  try {
    const res = await loginApi(form)
    if (res.success) {
      store.setToken(res.data as string)
      await store.fetchUserInfo()
      ElMessage.success({ message: '登录成功', duration: 2000 })
      router.push('/')
    } else {
      ElMessage.error({ message: res.errorMsg || '登录失败', duration: 2000 })
    }
  } catch {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-[calc(100vh-8rem)] flex items-center justify-center px-4">
    <div class="w-full max-w-md">
      <!-- Card -->
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
        <!-- Header -->
        <div class="text-center mb-8">
          <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg mx-auto mb-4">
            A
          </div>
          <h1 class="text-2xl font-bold text-gray-800">欢迎回来</h1>
          <p class="text-sm text-gray-400 mt-1">登录以管理你的博客</p>
        </div>

        <!-- Form -->
        <el-form @submit.prevent="handleLogin" class="space-y-5">
          <el-form-item label="用户名" label-width="80px" class="!mb-0">
            <el-input
              v-model="form.username"
              placeholder="请输入用户名"
              :prefix-icon="'User'"
              size="large"
              clearable
              @keyup.enter="handleLogin"
            />
          </el-form-item>

          <el-form-item label="密码" label-width="80px" class="!mb-0">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              :prefix-icon="'Lock'"
              size="large"
              show-password
              @keyup.enter="handleLogin"
            />
          </el-form-item>

          <el-button
            type="primary"
            size="large"
            class="!w-full !mt-6"
            :loading="loading"
            @click="handleLogin"
          >
            登 录
          </el-button>
        </el-form>

        <!-- Footer -->
        <div class="mt-6 text-center text-sm text-gray-400">
          还没有账号？
          <router-link to="/register" class="text-indigo-500 hover:text-indigo-600 font-medium">
            立即注册
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>
