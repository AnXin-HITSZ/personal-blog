<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getArticlesApi, addArticleApi, updateArticleApi } from '@/api/article'
import type { Article } from '@/types'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'

const route = useRoute()
const router = useRouter()

const articleId = computed(() => route.params.id ? Number(route.params.id) : null)
const isEdit = computed(() => articleId.value !== null)

const form = ref<Article>({ title: '', content: '' })
const loading = ref(false)
const saving = ref(false)

const previewHtml = computed(() => {
  if (!form.value.content) return '<p style="color: #9ca3af;">预览区域，开始编写内容...</p>'
  return marked(form.value.content, { async: false }) as string
})

onMounted(async () => {
  if (!isEdit.value) return
  loading.value = true
  try {
    const res = await getArticlesApi()
    if (res.success) {
      const list = res.data ?? []
      const found = list.find((a) => a.articleId === articleId.value)
      if (found) {
        form.value = { ...found }
      } else {
        ElMessage.warning('文章不存在')
        router.push('/admin')
      }
    }
  } catch {
    // handled by interceptor
  } finally {
    loading.value = false
  }
})

async function handleSave() {
  if (!form.value.title?.trim()) {
    ElMessage.warning('请输入文章标题')
    return
  }
  if (!form.value.content?.trim()) {
    ElMessage.warning('请输入文章内容')
    return
  }

  saving.value = true
  try {
    let res
    if (isEdit.value) {
      res = await updateArticleApi(form.value)
    } else {
      res = await addArticleApi(form.value)
    }
    if (res.success) {
      ElMessage.success(isEdit.value ? '文章已更新' : '文章已发布')
      router.push('/admin')
    } else {
      ElMessage.error(res.errorMsg || '保存失败')
    }
  } catch {
    // handled by interceptor
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="max-w-6xl mx-auto px-4 py-8">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">
          {{ isEdit ? '编辑文章' : '写文章' }}
        </h1>
        <p class="text-sm text-gray-400 mt-1">{{ isEdit ? '修改已有文章' : '创建一篇新文章' }}</p>
      </div>
      <div class="flex items-center gap-3">
        <el-button @click="router.push('/admin')">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">
          {{ isEdit ? '保存修改' : '发布文章' }}
        </el-button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="animate-pulse space-y-4 py-12">
      <div class="h-10 bg-gray-100 rounded w-1/2" />
      <div class="h-64 bg-gray-100 rounded" />
    </div>

    <template v-else>
      <!-- Title -->
      <el-input
        v-model="form.title"
        placeholder="输入文章标题..."
        size="large"
        maxlength="200"
        class="!text-xl font-bold !mb-6"
        :class="{ 'no-border': true }"
      />

      <!-- Editor area -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <!-- Input -->
        <div class="bg-white rounded-xl border border-gray-100 overflow-hidden">
          <div class="px-4 py-2 border-b border-gray-50 bg-gray-50/50">
            <span class="text-xs text-gray-400 font-medium">编辑 (Markdown)</span>
          </div>
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="24"
            placeholder="使用 Markdown 语法编写文章内容…"
            resize="none"
            class="!border-0"
          />
        </div>

        <!-- Preview -->
        <div class="bg-white rounded-xl border border-gray-100 overflow-hidden">
          <div class="px-4 py-2 border-b border-gray-50 bg-gray-50/50">
            <span class="text-xs text-gray-400 font-medium">预览</span>
          </div>
          <div class="p-6 overflow-y-auto max-h-[calc(24*1.5rem+3rem)]">
            <div
              class="markdown-body"
              v-html="previewHtml"
            />
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.no-border .el-input__wrapper {
  box-shadow: none !important;
  padding-left: 0;
}
.no-border .el-input__inner {
  font-size: 1.5rem;
  font-weight: 700;
}
:deep(.el-textarea__inner) {
  border: none !important;
  box-shadow: none !important;
  padding: 1.25rem;
  font-size: 0.9375rem;
  line-height: 1.75;
  min-height: 480px;
}
:deep(.el-textarea__inner:focus) {
  box-shadow: none !important;
}
</style>
