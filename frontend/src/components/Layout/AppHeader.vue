<template>
  <header class="bg-white shadow-sm border-b border-gray-200">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-16">
        <!-- Logo -->
        <div class="flex items-center">
          <router-link to="/" class="flex items-center">
            <div class="h-8 w-8 rounded-full bg-gradient-to-r from-blue-600 to-purple-600"></div>
            <span class="ml-3 text-xl font-bold text-gray-900">Personal Blog</span>
          </router-link>
        </div>

        <!-- Navigation -->
        <nav class="hidden md:flex items-center space-x-8">
          <router-link
            v-for="item in navItems"
            :key="item.name"
            :to="item.path"
            class="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200"
            :class="{ 'text-blue-600 font-semibold': $route.path === item.path }"
          >
            {{ item.name }}
          </router-link>
        </nav>

        <!-- User menu -->
        <div class="flex items-center space-x-4">
          <el-dropdown v-if="isAuthenticated" @command="handleCommand">
            <div class="flex items-center space-x-2 cursor-pointer">
              <div class="h-8 w-8 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-sm">
                {{ userInitial }}
              </div>
              <span class="text-gray-700 text-sm font-medium">{{ username }}</span>
              <el-icon class="text-gray-500"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>
                  <span class="ml-2">Profile</span>
                </el-dropdown-item>
                <el-dropdown-item command="settings">
                  <el-icon><Setting /></el-icon>
                  <span class="ml-2">Settings</span>
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  <span class="ml-2">Logout</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>

          <template v-else>
            <router-link to="/login">
              <el-button type="text" class="text-gray-700 hover:text-gray-900">
                Sign In
              </el-button>
            </router-link>
            <router-link to="/register">
              <el-button type="primary" class="ml-2">
                Sign Up
              </el-button>
            </router-link>
          </template>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ArrowDown, User, Setting, SwitchButton } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const navItems = [
  { name: 'Home', path: '/' },
  { name: 'Articles', path: '/articles' },
  { name: 'Categories', path: '/categories' },
  { name: 'About', path: '/about' }
]

const isAuthenticated = computed(() => !!authStore.token)
const username = computed(() => authStore.userInfo?.username || 'User')
const userInitial = computed(() => username.value.charAt(0).toUpperCase())

const handleCommand = (command: string) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'settings':
      // TODO: Implement settings page
      break
    case 'logout':
      authStore.logout()
      router.push('/login')
      break
  }
}
</script>