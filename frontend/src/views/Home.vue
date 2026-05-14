<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getArticlesApi } from '@/api/article'
import type { Article } from '@/types'
import ArticleCard from '@/components/ArticleCard.vue'
import { useUserStore } from '@/stores/user'

const store = useUserStore()
const articles = ref<Article[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await getArticlesApi()
    if (res.success) {
      articles.value = res.data ?? []
    }
  } catch {
    // handled by interceptor
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <!-- Hero -->
    <section class="relative overflow-hidden bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      <div class="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiM0ZjQ2ZTUiIGZpbGwtb3BhY2l0eT0iMC4wMyI+PHBhdGggZD0iTTM2IDE4YzEuNjU3IDAgMyAxLjM0MyAzIDNzLTEuMzQzIDMtMyAzLTMtMS4zNDMtMy0zIDEuMzQzLTMgMy0zeiIvPjwvZz48L2c+PC9zdmc+')] opacity-40" />
      <div class="max-w-6xl mx-auto px-4 py-20 md:py-28 relative">
        <div class="text-center max-w-2xl mx-auto">
          <h1 class="text-4xl md:text-5xl font-bold text-gray-900 mb-4 tracking-tight">
            欢迎来到 <span class="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-600">AnXin Blog</span>
          </h1>
          <p class="text-lg text-gray-500 leading-relaxed">
            分享技术思考、项目经验与生活感悟。<br class="hidden sm:block" />
            用文字记录成长的点滴。
          </p>
          <div class="mt-8 flex items-center justify-center gap-4">
            <router-link :to="store.isLoggedIn ? '/admin/editor' : '/register'">
              <el-button type="primary" size="large" round>
                开始写作
                <el-icon class="ml-1"><Edit /></el-icon>
              </el-button>
            </router-link>
            <el-tag type="info" effect="plain" round>
              {{ articles.length }} 篇文章
            </el-tag>
          </div>
        </div>
      </div>
      <div class="h-1 bg-gradient-to-r from-indigo-200 via-purple-200 to-pink-200" />
    </section>

    <!-- Article list -->
    <section class="max-w-6xl mx-auto px-4 py-12">
      <div class="flex items-center justify-between mb-8">
        <h2 class="text-2xl font-bold text-gray-800">最新文章</h2>
        <el-tag effect="plain" round>{{ articles.length }} 篇</el-tag>
      </div>

      <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div v-for="i in 6" :key="i" class="bg-white rounded-xl border border-gray-100 p-6 animate-pulse">
          <div class="h-3 bg-gray-100 rounded w-1/3 mb-4" />
          <div class="h-5 bg-gray-100 rounded w-3/4 mb-3" />
          <div class="space-y-2">
            <div class="h-3 bg-gray-100 rounded" />
            <div class="h-3 bg-gray-100 rounded w-5/6" />
          </div>
        </div>
      </div>

      <div
        v-else-if="articles.length === 0"
        class="text-center py-20"
      >
        <el-icon class="text-5xl text-gray-200 mb-4"><Document /></el-icon>
        <p class="text-gray-400">还没有文章，快来写下第一篇吧</p>
        <router-link to="/admin/editor">
          <el-button type="primary" class="mt-4">写文章</el-button>
        </router-link>
      </div>

      <transition-group
        v-else
        name="slide-up"
        tag="div"
        class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
      >
        <ArticleCard v-for="article in articles" :key="article.articleId" :article="article" />
      </transition-group>
    </section>
  </div>
</template>
