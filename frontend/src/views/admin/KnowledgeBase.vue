<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  uploadFileApi,
  listFilesApi,
  deleteSourceApi,
  indexDirectoryApi,
  getRagStatsApi,
} from '@/api/agent'
import type { KnowledgeBaseFile } from '@/types'

// ─── 状态 ───
const loading = ref(true)
const uploading = ref(false)
const reindexing = ref(false)
const files = ref<KnowledgeBaseFile[]>([])
const stats = ref({ total_files: 0, vector_dim: 0, collection: '' })
const dragOver = ref(false)

// ─── 生命周期 ───
onMounted(async () => {
  await Promise.all([fetchFiles(), fetchStats()])
  loading.value = false
})

// ─── 获取文件列表 ───
async function fetchFiles() {
  try {
    const res = await listFilesApi()
    if (res.success) {
      // Spring Boot 代理返回结构: data = FastAPI 响应 { code, message, data: [] }
      const fastapiData = res.data as any
      files.value = fastapiData?.data ?? res.data ?? []
    }
  } catch {
    // handled by interceptor
  }
}

// ─── 获取知识库统计 ───
async function fetchStats() {
  try {
    const res = await getRagStatsApi()
    if (res.success) {
      const fastapiData = res.data as any
      const s = fastapiData?.data ?? res.data
      if (s?.total_entities !== undefined) {
        stats.value = {
          total_files: s.total_entities ?? 0,
          vector_dim: s.vector_dim ?? 0,
          collection: s.collection ?? '',
        }
      }
    }
  } catch {
    // ignore
  }
}

// ─── 上传文件 ───
async function handleUpload(file: File) {
  // 验证扩展名
  const ext = file.name.split('.').pop()?.toLowerCase()
  if (!ext || !['txt', 'md'].includes(ext)) {
    ElMessage.warning('仅支持 .txt 和 .md 文件')
    return
  }
  // 验证大小 (10MB)
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.warning('文件大小不能超过 10MB')
    return
  }

  uploading.value = true
  try {
    const res = await uploadFileApi(file)
    if (res.success) {
      ElMessage.success(`「${file.name}」上传成功并已建立索引`)
      await Promise.all([fetchFiles(), fetchStats()])
    } else {
      ElMessage.error(res.errorMsg || '上传失败')
    }
  } catch {
    // handled by interceptor
  } finally {
    uploading.value = false
  }
}

// ─── 拖拽上传 ───
function onDragOver(e: DragEvent) {
  e.preventDefault()
  dragOver.value = true
}
function onDragLeave() {
  dragOver.value = false
}
function onDrop(e: DragEvent) {
  e.preventDefault()
  dragOver.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) handleUpload(file)
}

// ─── 选择文件上传 ───
const fileInput = ref<HTMLInputElement | null>(null)
function triggerFileInput() {
  fileInput.value?.click()
}
function onFileSelected(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    handleUpload(file)
    target.value = '' // 允许重复选择同一文件
  }
}

// ─── 删除文件索引 ───
async function handleDelete(file: KnowledgeBaseFile) {
  try {
    await ElMessageBox.confirm(
      `确定要删除「${file.filename}」的向量索引吗？文件本身不会被删除。`,
      '删除确认',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' },
    )
    const res = await deleteSourceApi(file.file_path)
    if (res.success) {
      ElMessage.success(`「${file.filename}」索引已删除`)
      await Promise.all([fetchFiles(), fetchStats()])
    } else {
      ElMessage.error(res.errorMsg || '删除失败')
    }
  } catch {
    // canceled or error
  }
}

// ─── 重新索引所有文件 ───
async function handleReindex() {
  try {
    await ElMessageBox.confirm(
      '将重新索引知识库目录下的所有文件，已有索引会被覆盖。确定继续？',
      '重新索引',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'info' },
    )
    reindexing.value = true
    const res = await indexDirectoryApi()
    if (res.success) {
      ElMessage.success('知识库重新索引完成')
      await Promise.all([fetchFiles(), fetchStats()])
    } else {
      ElMessage.error(res.errorMsg || '重新索引失败')
    }
  } catch {
    // canceled or error
  } finally {
    reindexing.value = false
  }
}

// ─── 格式化文件大小 ───
function formatSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

// ─── 格式化时间 ───
function formatTime(iso: string): string {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN')
}
</script>

<template>
  <div class="max-w-6xl mx-auto px-4 py-8">
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">知识库管理</h1>
        <p class="text-sm text-gray-400 mt-1">上传文档并建立向量索引，为 AI 问答提供知识来源</p>
      </div>
      <div class="flex items-center gap-2">
        <el-button
          plain
          :loading="reindexing"
          :disabled="uploading"
          @click="handleReindex"
        >
          <el-icon><Refresh /></el-icon>
          重新索引
        </el-button>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
      <div class="bg-white rounded-xl border border-gray-100 p-5">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-500">
            <el-icon class="text-xl"><Document /></el-icon>
          </div>
          <div>
            <p class="text-xs text-gray-400">向量总数</p>
            <p class="text-xl font-bold text-gray-800">{{ stats.total_files }}</p>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-xl border border-gray-100 p-5">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-emerald-50 flex items-center justify-center text-emerald-500">
            <el-icon class="text-xl"><Connection /></el-icon>
          </div>
          <div>
            <p class="text-xs text-gray-400">向量维度</p>
            <p class="text-xl font-bold text-gray-800">{{ stats.vector_dim || '-' }}</p>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-xl border border-gray-100 p-5">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-amber-50 flex items-center justify-center text-amber-500">
            <el-icon class="text-xl"><Files /></el-icon>
          </div>
          <div>
            <p class="text-xs text-gray-400">上传文件数</p>
            <p class="text-xl font-bold text-gray-800">{{ files.length }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Upload zone -->
    <div
      class="mb-8"
      @dragover="onDragOver"
      @dragleave="onDragLeave"
      @drop="onDrop"
    >
      <div
        :class="[
          dragOver
            ? 'border-indigo-400 bg-indigo-50'
            : 'border-gray-200 bg-gray-50',
          'border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors',
        ]"
        @click="triggerFileInput"
      >
        <el-icon
          class="text-4xl"
          :class="dragOver ? 'text-indigo-500' : 'text-gray-300'"
        >
          <UploadFilled />
        </el-icon>
        <p
          class="mt-2 text-sm"
          :class="dragOver ? 'text-indigo-600' : 'text-gray-400'"
        >
          {{ uploading ? '正在上传并索引...' : dragOver ? '释放文件以上传' : '拖拽文件到此处，或点击选择文件' }}
        </p>
        <p class="mt-1 text-xs text-gray-300">
          支持 .txt 和 .md 格式，单个文件不超过 10MB
        </p>
      </div>
      <input
        ref="fileInput"
        type="file"
        accept=".txt,.md"
        class="hidden"
        @change="onFileSelected"
      />
    </div>

    <!-- Loading -->
    <div v-if="loading" class="bg-white rounded-xl border border-gray-100 p-8 text-center">
      <el-icon class="text-2xl text-gray-300 animate-spin"><Loading /></el-icon>
      <p class="mt-2 text-sm text-gray-400">加载中...</p>
    </div>

    <!-- File list -->
    <div v-else class="bg-white rounded-xl border border-gray-100 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-50">
        <h2 class="font-semibold text-gray-700">已上传文件</h2>
      </div>

      <el-table
        :data="files"
        stripe
        empty-text="还没有上传文件，拖拽或点击上方区域上传"
        style="width: 100%"
      >
        <el-table-column label="文件名" min-width="280">
          <template #default="{ row }">
            <div class="flex items-center gap-2">
              <el-icon class="text-gray-400">
                <Tickets />
              </el-icon>
              <span class="text-gray-700">{{ row.filename }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="size" label="大小" width="120">
          <template #default="{ row }">
            <span class="text-gray-400 text-sm">{{ formatSize(row.size) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="last_modified" label="上传时间" width="180">
          <template #default="{ row }">
            <span class="text-gray-400 text-sm">{{ formatTime(row.last_modified) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              size="small"
              type="danger"
              plain
              :loading="uploading"
              @click="handleDelete(row)"
            >
              删除索引
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>
