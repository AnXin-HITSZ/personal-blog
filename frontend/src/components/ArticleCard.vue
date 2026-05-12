<script setup lang="ts">
import type { Article } from '@/types'
import { computed } from 'vue'

const props = defineProps<{ article: Article }>()

const timeAgo = computed(() => {
  if (!props.article.createTime) return ''
  const date = new Date(props.article.createTime)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes} 分钟前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} 小时前`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days} 天前`
  return date.toLocaleDateString('zh-CN')
})

const excerpt = computed(() => {
  const text = props.article.content?.replace(/<[^>]+>/g, '').replace(/[#*`\[\]]/g, '') ?? ''
  return text.length > 150 ? text.slice(0, 150) + '…' : text
})
</script>

<template>
  <router-link
    :to="`/article/${article.articleId}`"
    class="block group"
  >
    <article
      class="bg-white rounded-xl border border-gray-100 p-6 transition-all duration-300
             hover:shadow-lg hover:shadow-indigo-100/50 hover:border-indigo-100
             hover:-translate-y-0.5"
    >
      <div class="flex items-center gap-2 text-xs text-gray-400 mb-3">
        <el-icon><Calendar /></el-icon>
        <span>{{ timeAgo }}</span>
      </div>

      <h2
        class="text-lg font-semibold text-gray-800 mb-2 transition-colors
               group-hover:text-indigo-600 line-clamp-1"
      >
        {{ article.title || '无标题' }}
      </h2>

      <p class="text-sm text-gray-500 leading-relaxed line-clamp-3">
        {{ excerpt }}
      </p>

      <div class="mt-4 flex items-center text-sm text-indigo-500 font-medium opacity-0 group-hover:opacity-100 transition-opacity">
        <span>阅读全文</span>
        <el-icon class="ml-1"><ArrowRight /></el-icon>
      </div>
    </article>
  </router-link>
</template>
