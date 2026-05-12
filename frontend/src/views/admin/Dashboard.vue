<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getArticlesApi, deleteArticleApi } from '@/api/article'
import { useUserStore } from '@/stores/user'
import type { Article } from '@/types'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const store = useUserStore()
const articles = ref<Article[]>([])
const loading = ref(true)

onMounted(async () => {
  await fetchArticles()
})

async function fetchArticles() {
  loading.value = true
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
}

const articleCount = computed(() => articles.value.length)

function goEditor(id?: number) {
  router.push(`/admin/editor/${id ?? ''}`)
}

async function handleDelete(id: number, title: string) {
  try {
    await ElMessageBox.confirm(
      `确定要删除「${title}」吗？此操作不可恢复。`,
      '删除确认',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' },
    )
    const res = await deleteArticleApi(id)
    if (res.success) {
      ElMessage.success('删除成功')
      await fetchArticles()
    } else {
      ElMessage.error(res.errorMsg || '删除失败')
    }
  } catch {
    // canceled or error
  }
}
</script>

<template>
  <div class="max-w-6xl mx-auto px-4 py-8">
    <!-- Page header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">管理后台</h1>
        <p class="text-sm text-gray-400 mt-1">管理你的博客文章</p>
      </div>
      <el-button type="primary" size="large" @click="goEditor()">
        <el-icon><Plus /></el-icon>
        写文章
      </el-button>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
      <div class="bg-white rounded-xl border border-gray-100 p-5">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-500">
            <el-icon class="text-xl"><Document /></el-icon>
          </div>
          <div>
            <p class="text-xs text-gray-400">文章总数</p>
            <p class="text-xl font-bold text-gray-800">{{ articleCount }}</p>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-xl border border-gray-100 p-5">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-emerald-50 flex items-center justify-center text-emerald-500">
            <el-icon class="text-xl"><UserFilled /></el-icon>
          </div>
          <div>
            <p class="text-xs text-gray-400">当前用户</p>
            <p class="text-xl font-bold text-gray-800">{{ store.username }}</p>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-xl border border-gray-100 p-5">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-amber-50 flex items-center justify-center text-amber-500">
            <el-icon class="text-xl"><Clock /></el-icon>
          </div>
          <div>
            <p class="text-xs text-gray-400">最近更新</p>
            <p class="text-sm font-medium text-gray-800" v-if="articles.length">
              {{ new Date(articles[0]?.updateTime ?? articles[0]?.createTime ?? '').toLocaleDateString('zh-CN') }}
            </p>
            <p class="text-sm text-gray-400" v-else>-</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Article table -->
    <div class="bg-white rounded-xl border border-gray-100 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-50">
        <h2 class="font-semibold text-gray-700">文章列表</h2>
      </div>

      <div v-if="loading" class="p-8 text-center text-gray-400">
        <el-icon class="text-2xl animate-spin"><Loading /></el-icon>
        <p class="mt-2 text-sm">加载中...</p>
      </div>

      <el-table
        v-else
        :data="articles"
        stripe
        empty-text="还没有文章，点击右上角开始写作"
        style="width: 100%"
      >
        <el-table-column type="index" label="#" width="60" />
        <el-table-column prop="title" label="标题" min-width="240">
          <template #default="{ row }">
            <span class="text-gray-700 font-medium">{{ row.title || '无标题' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="createTime" label="创建时间" width="180">
          <template #default="{ row }">
            <span class="text-gray-400 text-sm">
              {{ row.createTime ? new Date(row.createTime).toLocaleString('zh-CN') : '-' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="updateTime" label="更新时间" width="180">
          <template #default="{ row }">
            <span class="text-gray-400 text-sm">
              {{ row.updateTime ? new Date(row.updateTime).toLocaleString('zh-CN') : '-' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="goEditor(row.articleId)">
              编辑
            </el-button>
            <el-button
              size="small"
              type="danger"
              plain
              @click="handleDelete(row.articleId!, row.title)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>
