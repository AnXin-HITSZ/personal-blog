<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { registerApi } from '@/api/user'
import type { RegisterForm } from '@/types'
import { ElMessage } from 'element-plus'

const router = useRouter()

const form = reactive<RegisterForm>({
  username: '',
  password: '',
  confirmedPassword: '',
})
const loading = ref(false)

async function handleRegister() {
  if (!form.username.trim()) {
    ElMessage.warning('请输入用户名')
    return
  }
  if (form.username.length > 100) {
    ElMessage.warning('用户名长度不能超过 100 个字符')
    return
  }
  if (!form.password) {
    ElMessage.warning('请输入密码')
    return
  }
  if (form.password.length > 100) {
    ElMessage.warning('密码长度不能超过 100 个字符')
    return
  }
  if (form.password !== form.confirmedPassword) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }

  loading.value = true
  try {
    const res = await registerApi(form)
    if (res.success) {
      ElMessage.success('注册成功，请登录')
      router.push('/login')
    } else {
      ElMessage.error(res.errorMsg || '注册失败')
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
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
        <!-- Header -->
        <div class="text-center mb-8">
          <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg mx-auto mb-4">
            A
          </div>
          <h1 class="text-2xl font-bold text-gray-800">创建账号</h1>
          <p class="text-sm text-gray-400 mt-1">注册后即可发布和管理文章</p>
        </div>

        <!-- Form -->
        <el-form @submit.prevent="handleRegister" class="space-y-5">
          <el-form-item label="用户名" class="!mb-0">
            <el-input
              v-model="form.username"
              placeholder="请输入用户名"
              :prefix-icon="'User'"
              size="large"
              clearable
              maxlength="100"
            />
          </el-form-item>

          <el-form-item label="密码" class="!mb-0">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="请设置密码"
              :prefix-icon="'Lock'"
              size="large"
              show-password
              maxlength="100"
            />
          </el-form-item>

          <el-form-item label="确认密码" class="!mb-0">
            <el-input
              v-model="form.confirmedPassword"
              type="password"
              placeholder="请再次输入密码"
              :prefix-icon="'Lock'"
              size="large"
              show-password
              maxlength="100"
            />
          </el-form-item>

          <el-button
            type="primary"
            size="large"
            class="!w-full !mt-6"
            :loading="loading"
            @click="handleRegister"
          >
            注 册
          </el-button>
        </el-form>

        <div class="mt-6 text-center text-sm text-gray-400">
          已有账号？
          <router-link to="/login" class="text-indigo-500 hover:text-indigo-600 font-medium">
            立即登录
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>
