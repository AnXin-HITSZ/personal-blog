<template>
  <div class="flex flex-col h-full">
    <!-- Header -->
    <div class="px-3 py-3 border-b border-gray-200">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-bold text-gray-700 tracking-wide uppercase">历史对话</h3>
        <el-button
          size="small"
          type="primary"
          :icon="Plus"
          circle
          @click="$emit('new-chat')"
          title="新建对话"
        />
      </div>
      <!-- Search -->
      <el-input
        v-model="searchQuery"
        size="small"
        placeholder="搜索历史对话..."
        clearable
        class="mt-2"
        :prefix-icon="Search"
      />
    </div>

    <!-- Session List -->
    <div class="flex-1 overflow-y-auto py-2 px-2 space-y-1">
      <div
        v-if="filteredSessions.length === 0"
        class="text-center py-8 text-gray-400"
      >
        <svg class="w-8 h-8 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
          <path stroke-linecap="round" stroke-linejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
        <p class="text-sm">{{ searchQuery ? '没有匹配的对话' : '暂无历史对话' }}</p>
      </div>
      <div
        v-for="session in filteredSessions"
        :key="session.sessionId"
        class="group rounded-lg cursor-pointer transition-all duration-150"
        :class="isActive(session.sessionId) ? 'bg-blue-50 border border-blue-200 shadow-sm' : 'border border-transparent hover:bg-gray-50 hover:border-gray-200'"
        @click="$emit('select-session', session)"
      >
        <div class="px-3 py-2.5">
          <div class="flex items-start justify-between">
            <div class="min-w-0 flex-1">
              <!-- Title -->
              <div class="flex items-center gap-1.5">
                <svg class="w-3.5 h-3.5 text-gray-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
                <span v-if="editingId === session.sessionId" class="flex-1">
                  <el-input
                    ref="editInputRef"
                    v-model="editTitle"
                    size="small"
                    @blur="confirmRename(session)"
                    @keydown.enter.prevent="confirmRename(session)"
                    @keydown.escape.prevent="cancelRename"
                    @click.stop
                    autofocus
                  />
                </span>
                <span v-else class="text-sm font-medium text-gray-800 truncate block max-w-[140px]">{{ session.title }}</span>
              </div>
              <!-- Preview -->
              <p v-if="session.preview" class="text-xs text-gray-400 mt-1 truncate">{{ session.preview }}</p>
              <!-- Meta -->
              <div class="flex items-center gap-2 mt-1">
                <span class="text-[11px] text-gray-400">{{ formatTime(session.createdAt) }}</span>
                <span class="text-[11px] text-gray-300">·</span>
                <span class="text-[11px] text-gray-400">{{ session.messageCount }} 条消息</span>
              </div>
            </div>
            <!-- Actions -->
            <div class="flex gap-0.5 shrink-0 ml-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <el-button
                size="small"
                :icon="Edit"
                circle
                @click.stop="startRename(session)"
              />
              <el-button
                size="small"
                type="danger"
                :icon="Delete"
                circle
                @click.stop="$emit('delete-session', session)"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Plus, Search, Edit, Delete } from '@element-plus/icons-vue'
import type { SessionDTO } from '@/types/api'

const props = defineProps<{
  sessions: SessionDTO[]
  activeSessionId: string
}>()

const emit = defineEmits<{
  'select-session': [session: SessionDTO]
  'delete-session': [session: SessionDTO]
  'rename-session': [sessionId: string, title: string]
  'new-chat': []
}>()

const searchQuery = ref('')
const editingId = ref<string | null>(null)
const editTitle = ref('')
const editInputRef = ref<HTMLInputElement>()

const filteredSessions = computed(() => {
  if (!searchQuery.value.trim()) return props.sessions
  const q = searchQuery.value.trim().toLowerCase()
  return props.sessions.filter(
    s => s.title?.toLowerCase().includes(q) || s.preview?.toLowerCase().includes(q)
  )
})

const isActive = (sessionId: string) => sessionId === props.activeSessionId

const formatTime = (timestamp: number) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } else if (days === 1) {
    return '昨天'
  } else if (days < 7) {
    return `${days}天前`
  } else {
    return date.toLocaleDateString([], { month: 'short', day: 'numeric' })
  }
}

const startRename = (session: SessionDTO) => {
  editingId.value = session.sessionId
  editTitle.value = session.title
  setTimeout(() => {
    const input = document.querySelector<HTMLInputElement>('.el-input__inner')
    input?.focus()
  }, 50)
}

const confirmRename = (session: SessionDTO) => {
  const title = editTitle.value.trim()
  if (title && title !== session.title) {
    emit('rename-session', session.sessionId, title)
  }
  editingId.value = null
  editTitle.value = ''
}

const cancelRename = () => {
  editingId.value = null
  editTitle.value = ''
}
</script>
