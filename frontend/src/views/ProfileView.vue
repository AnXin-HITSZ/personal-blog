<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
    <nav class="bg-white shadow-sm border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex items-center">
            <router-link to="/" class="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
              ← Back to Home
            </router-link>
          </div>
          <div class="flex items-center space-x-4">
            <router-link to="/" class="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
              Home
            </router-link>
            <el-button type="primary" @click="handleLogout" class="ml-4">
              Logout
            </el-button>
          </div>
        </div>
      </div>
    </nav>

    <main class="max-w-4xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
      <div class="bg-white shadow-xl rounded-lg overflow-hidden">
        <!-- Profile Header -->
        <div class="bg-gradient-to-r from-blue-600 to-purple-600 px-8 py-12">
          <div class="flex items-center">
            <div class="h-24 w-24 rounded-full bg-white flex items-center justify-center text-4xl font-bold text-blue-600">
              {{ userInfo?.username?.charAt(0).toUpperCase() || 'U' }}
            </div>
            <div class="ml-8">
              <h1 class="text-3xl font-bold text-white">{{ userInfo?.username || 'Loading...' }}</h1>
              <p class="text-blue-100 mt-2">Member since {{ joinDate }}</p>
            </div>
          </div>
        </div>

        <!-- Profile Content -->
        <div class="px-8 py-8">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
            <!-- Personal Information -->
            <div>
              <h2 class="text-xl font-semibold text-gray-900 mb-4">Personal Information</h2>
              <div class="space-y-4">
                <div class="flex items-center">
                  <div class="w-8">
                    <el-icon class="text-gray-500"><User /></el-icon>
                  </div>
                  <div class="ml-4">
                    <p class="text-sm text-gray-500">Username</p>
                    <p class="font-medium">{{ userInfo?.username || 'N/A' }}</p>
                  </div>
                </div>
                <div class="flex items-center">
                  <div class="w-8">
                    <el-icon class="text-gray-500"><Key /></el-icon>
                  </div>
                  <div class="ml-4">
                    <p class="text-sm text-gray-500">User ID</p>
                    <p class="font-medium">{{ userInfo?.userId || 'N/A' }}</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Account Statistics -->
            <div>
              <h2 class="text-xl font-semibold text-gray-900 mb-4">Account Statistics</h2>
              <div class="grid grid-cols-2 gap-4">
                <div class="bg-blue-50 rounded-lg p-4">
                  <p class="text-sm text-blue-600">Articles Published</p>
                  <p class="text-2xl font-bold text-blue-900">12</p>
                </div>
                <div class="bg-green-50 rounded-lg p-4">
                  <p class="text-sm text-green-600">Total Views</p>
                  <p class="text-2xl font-bold text-green-900">1.2K</p>
                </div>
                <div class="bg-purple-50 rounded-lg p-4">
                  <p class="text-sm text-purple-600">Comments</p>
                  <p class="text-2xl font-bold text-purple-900">48</p>
                </div>
                <div class="bg-yellow-50 rounded-lg p-4">
                  <p class="text-sm text-yellow-600">Likes</p>
                  <p class="text-2xl font-bold text-yellow-900">256</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Recent Activity -->
          <div class="mt-12">
            <h2 class="text-xl font-semibold text-gray-900 mb-4">Recent Activity</h2>
            <div class="border border-gray-200 rounded-lg overflow-hidden">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                  <tr>
                    <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Article
                    </th>
                    <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date
                    </th>
                    <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Views
                    </th>
                    <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr v-for="activity in recentActivities" :key="activity.id">
                    <td class="px-6 py-4 whitespace-nowrap">
                      <div class="font-medium text-gray-900">{{ activity.title }}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {{ activity.date }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {{ activity.views }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                      <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                        {{ activity.status }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Key } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const userInfo = ref<any>(null)
const joinDate = ref('April 2026')
const recentActivities = ref([
  { id: 1, title: 'Getting Started with Vue 3', date: '2026-04-18', views: 156, status: 'Published' },
  { id: 2, title: 'TypeScript Best Practices', date: '2026-04-15', views: 89, status: 'Published' },
  { id: 3, title: 'Building Scalable APIs', date: '2026-04-12', views: 203, status: 'Published' },
  { id: 4, title: 'Modern CSS Techniques', date: '2026-04-10', views: 67, status: 'Draft' }
])

const handleLogout = () => {
  localStorage.removeItem('token')
  ElMessage.success('Logged out successfully')
  router.push('/login')
}

onMounted(async () => {
  try {
    await authStore.getUserInfo()
    userInfo.value = authStore.userInfo
    // In a real app, you would fetch join date from API
    joinDate.value = 'April 2026'
  } catch (error) {
    ElMessage.error('Failed to load user information')
  }
})
</script>