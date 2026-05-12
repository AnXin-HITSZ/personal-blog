<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getArticlesApi } from '@/api/article'
import { useUserStore } from '@/stores/user'
import type { Article } from '@/types'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'

const route = useRoute()
const router = useRouter()
const store = useUserStore()

const article = ref<Article | null>(null)
const loading = ref(true)

const renderedContent = computed(() => {
  if (!article.value?.content) return ''
  return marked(article.value.content, { async: false }) as string
})

const formattedDate = computed(() => {
  if (!article.value?.createTime) return ''
  const d = new Date(article.value.createTime)
  return d.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
})

onMounted(async () => {
  try {
    const res = await getArticlesApi()
    if (res.success) {
      const list = res.data ?? []
      const found = list.find((a) => a.articleId === Number(route.params.id))
      if (found) {
        article.value = found
      } else {
        ElMessage.warning('文章不存在')
        router.push('/')
      }
    }
  } catch {
    // handled by interceptor
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div v-if="loading" class="max-w-3xl mx-auto px-4 py-12">
    <div class="animate-pulse space-y-4">
      <div class="h-8 bg-gray-100 rounded w-2/3" />
      <div class="h-4 bg-gray-100 rounded w-1/4" />
      <div class="space-y-3 mt-8">
        <div class="h-4 bg-gray-100 rounded" />
        <div class="h-4 bg-gray-100 rounded w-5/6" />
        <div class="h-4 bg-gray-100 rounded w-4/6" />
      </div>
    </div>
  </div>

  <article v-else-if="article" class="max-w-3xl mx-auto px-4 py-12">
    <!-- Back -->
    <button
      class="flex items-center gap-1 text-sm text-gray-400 hover:text-indigo-500 transition-colors mb-8"
      @click="router.push('/')"
    >
      <el-icon><ArrowLeft /></el-icon>
      返回首页
    </button>

    <!-- Header -->
    <header class="mb-10">
      <h1 class="text-3xl md:text-4xl font-bold text-gray-900 mb-4 leading-tight">
        {{ article.title }}
      </h1>
      <div class="flex items-center gap-4 text-sm text-gray-400">
        <span class="flex items-center gap-1">
          <el-icon><Calendar /></el-icon>
          {{ formattedDate }}
        </span>
        <span v-if="article.updateTime && article.updateTime !== article.createTime" class="flex items-center gap-1">
          <el-icon><Refresh /></el-icon>
          更新于 {{ new Date(article.updateTime).toLocaleDateString('zh-CN') }}
        </span>
      </div>
    </header>

    <!-- Divider -->
    <div class="h-px bg-gradient-to-r from-indigo-200 via-purple-200 to-transparent mb-10" />

    <!-- Content -->
    <div
      class="markdown-body text-gray-700 leading-relaxed text-base"
      v-html="renderedContent"
    />

    <!-- Footer actions -->
    <div class="mt-12 pt-8 border-t border-gray-100 flex items-center gap-3">
      <router-link
        v-if="store.isLoggedIn"
        :to="`/admin/editor/${article.articleId}`"
      >
        <el-button size="small">
          <el-icon><Edit /></el-icon>
          编辑
        </el-button>
      </router-link>
    </div>
  </article>

  <div v-else class="text-center py-20 text-gray-400">
    文章不存在或已被删除
  </div>
</template>
