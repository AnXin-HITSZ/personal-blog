<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessageBox } from 'element-plus'
import { computed } from 'vue'

const router = useRouter()
const store = useUserStore()

const menuItems = computed(() => {
  const items = [
    { label: '首页', path: '/', icon: 'HomeFilled' },
    { label: '问答', path: '/qa', icon: 'ChatLineSquare' },
  ]
  if (store.isLoggedIn) {
    items.push({ label: '知识库', path: '/admin/knowledge-base', icon: 'Collection' })
    items.push({ label: 'SKILL', path: '/admin/skills', icon: 'MagicStick' })
    items.push({ label: '部署', path: '/admin/deploy', icon: 'Upload' })
    items.push({ label: '管理后台', path: '/admin', icon: 'Setting' })
  }
  return items
})

function handleLogout() {
  ElMessageBox.confirm('确认退出登录？', '提示', {
    confirmButtonText: '退出',
    cancelButtonText: '取消',
    type: 'info',
  }).then(() => {
    store.logout()
    router.push('/')
  }).catch(() => {})
}
</script>

<template>
  <header class="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
    <div class="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
      <!-- Logo -->
      <router-link to="/" class="flex items-center gap-2 group">
        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-sm group-hover:shadow-lg group-hover:shadow-indigo-200 transition-shadow">
          A
        </div>
        <span class="text-lg font-semibold text-gray-800">AnXin Blog</span>
      </router-link>

      <!-- Nav -->
      <nav class="flex items-center gap-1">
        <el-button
          v-for="item in menuItems"
          :key="item.path"
          :text="router.currentRoute.value.path !== item.path"
          :type="router.currentRoute.value.path === item.path ? 'primary' : 'default'"
          class="!px-4 !h-9"
          @click="router.push(item.path)"
        >
          {{ item.label }}
        </el-button>

        <!-- Auth buttons -->
        <div class="ml-3 pl-3 border-l border-gray-200 flex items-center gap-2">
          <template v-if="store.isLoggedIn">
            <el-button text class="!h-9">
              <el-icon><UserFilled /></el-icon>
              {{ store.username }}
            </el-button>
            <el-button size="small" @click="handleLogout">退出</el-button>
          </template>
          <template v-else>
            <router-link to="/login">
              <el-button text class="!h-9">登录</el-button>
            </router-link>
            <router-link to="/register">
              <el-button size="small" plain>注册</el-button>
            </router-link>
          </template>
        </div>
      </nav>
    </div>
  </header>
</template>
