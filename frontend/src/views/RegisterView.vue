<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-emerald-100 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <div class="text-center">
        <h2 class="mt-6 text-4xl font-extrabold text-gray-900">
          Create your account
        </h2>
        <p class="mt-2 text-sm text-gray-600">
          Or
          <router-link to="/login" class="font-medium text-green-600 hover:text-green-500">
            sign in to existing account
          </router-link>
        </p>
      </div>

      <div class="bg-white py-8 px-6 shadow-xl rounded-lg sm:px-10">
        <el-form
          ref="registerFormRef"
          :model="registerForm"
          :rules="registerRules"
          class="space-y-6"
          @submit.prevent="handleRegister"
        >
          <el-form-item prop="username">
            <el-input
              v-model="registerForm.username"
              placeholder="Username"
              size="large"
              :prefix-icon="User"
            />
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="registerForm.password"
              type="password"
              placeholder="Password"
              size="large"
              :prefix-icon="Lock"
              show-password
            />
          </el-form-item>

          <el-form-item prop="confirmedPassword">
            <el-input
              v-model="registerForm.confirmedPassword"
              type="password"
              placeholder="Confirm Password"
              size="large"
              :prefix-icon="Lock"
              show-password
            />
          </el-form-item>

          <div class="flex items-center">
            <el-checkbox v-model="agreeTerms">
              I agree to the
              <a href="#" class="text-green-600 hover:text-green-500 ml-1">Terms and Conditions</a>
            </el-checkbox>
          </div>

          <div>
            <el-button
              type="success"
              size="large"
              native-type="submit"
              class="w-full"
              :loading="loading"
            >
              Create Account
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

const registerFormRef = ref<FormInstance>()
const loading = ref(false)
const agreeTerms = ref(false)

const registerForm = reactive({
  username: '',
  password: '',
  confirmedPassword: ''
})

const validatePassword = (rule: any, value: any, callback: any) => {
  if (value === '') {
    callback(new Error('Please confirm password'))
  } else if (value !== registerForm.password) {
    callback(new Error('Two passwords do not match'))
  } else {
    callback()
  }
}

const registerRules = reactive<FormRules>({
  username: [
    { required: true, message: 'Please input username', trigger: 'blur' },
    { min: 3, max: 20, message: 'Length should be 3 to 20', trigger: 'blur' }
  ],
  password: [
    { required: true, message: 'Please input password', trigger: 'blur' },
    { min: 6, max: 30, message: 'Length should be 6 to 30', trigger: 'blur' }
  ],
  confirmedPassword: [
    { required: true, validator: validatePassword, trigger: 'blur' }
  ]
})

const handleRegister = async () => {
  if (!registerFormRef.value) return

  if (!agreeTerms.value) {
    ElMessage.warning('Please agree to the terms and conditions')
    return
  }

  const valid = await registerFormRef.value.validate()
  if (!valid) return

  loading.value = true
  try {
    await authStore.register(registerForm)
    ElMessage.success('Registration successful! Please login.')
    router.push('/login')
  } catch (error: any) {
    ElMessage.error(error.message || 'Registration failed')
  } finally {
    loading.value = false
  }
}
</script>