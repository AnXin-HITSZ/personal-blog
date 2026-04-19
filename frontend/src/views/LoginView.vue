<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <div class="text-center">
        <h2 class="mt-6 text-4xl font-extrabold text-gray-900">
          Sign in to your account
        </h2>
        <p class="mt-2 text-sm text-gray-600">
          Or
          <router-link to="/register" class="font-medium text-blue-600 hover:text-blue-500">
            create a new account
          </router-link>
        </p>
      </div>

      <div class="bg-white py-8 px-6 shadow-xl rounded-lg sm:px-10">
        <el-form
          ref="loginFormRef"
          :model="loginForm"
          :rules="loginRules"
          class="space-y-6"
          @submit.prevent="handleLogin"
        >
          <el-form-item prop="username">
            <el-input
              v-model="loginForm.username"
              placeholder="Username"
              size="large"
              :prefix-icon="User"
            />
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="Password"
              size="large"
              :prefix-icon="Lock"
              show-password
            />
          </el-form-item>

          <div class="flex items-center justify-between">
            <div class="flex items-center">
              <el-checkbox v-model="rememberMe">Remember me</el-checkbox>
            </div>
            <div class="text-sm">
              <a href="#" class="font-medium text-blue-600 hover:text-blue-500">
                Forgot your password?
              </a>
            </div>
          </div>

          <div>
            <el-button
              type="primary"
              size="large"
              native-type="submit"
              class="w-full"
              :loading="loading"
            >
              Sign in
            </el-button>
          </div>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElForm, ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const loginFormRef = ref<FormInstance>()
const loading = ref(false)
const rememberMe = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules = reactive<FormRules>({
  username: [
    { required: true, message: 'Please input username', trigger: 'blur' },
    { min: 3, max: 20, message: 'Length should be 3 to 20', trigger: 'blur' }
  ],
  password: [
    { required: true, message: 'Please input password', trigger: 'blur' },
    { min: 6, max: 30, message: 'Length should be 6 to 30', trigger: 'blur' }
  ]
})

const handleLogin = async () => {
  if (!loginFormRef.value) return

  const valid = await loginFormRef.value.validate()
  if (!valid) return

  loading.value = true
  try {
    await authStore.login(loginForm)
    ElMessage.success('Login successful')
    router.push('/')
  } catch (error: any) {
    ElMessage.error(error.message || 'Login failed')
  } finally {
    loading.value = false
  }
}
</script>