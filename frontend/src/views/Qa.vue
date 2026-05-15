<script setup lang="ts">
import { ref, nextTick, onMounted, watch } from 'vue'
import { marked } from 'marked'
import { markedHighlight } from 'marked-highlight'
import hljs from 'highlight.js'
import { streamChatApi, chatApi, clearSessionApi, fetchHistoryApi, listSessionsApi, deleteSessionApi } from '@/api/agent'

// 配置 marked 语法高亮
marked.use(markedHighlight({
  langPrefix: 'hljs language-',
  highlight(code: string, lang: string): string {
    const language = hljs.getLanguage(lang) ? lang : 'plaintext'
    try {
      return hljs.highlight(code, { language }).value
    } catch {
      return hljs.highlightAuto(code).value
    }
  },
}))
import type { ChatMessage, ToolCallEvent, SessionSummary } from '@/types'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Promotion } from '@element-plus/icons-vue'

// ─── 会话管理 ───
const SESSION_KEY = 'qa_session_id'
function getSessionId(): string {
  let sid = localStorage.getItem(SESSION_KEY)
  if (!sid) {
    sid = `session-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
    localStorage.setItem(SESSION_KEY, sid)
  }
  return sid
}
function saveSessionId(sid: string) {
  localStorage.setItem(SESSION_KEY, sid)
}

const sessionId = ref(getSessionId())

// ─── 状态 ───
const sessions = ref<SessionSummary[]>([])
const messages = ref<ChatMessage[]>([])
const loading = ref(true)
const sending = ref(false)
const streaming = ref(false)
const inputText = ref('')
const messageList = ref<HTMLElement | null>(null)
const toolCalls = ref<ToolCallEvent[]>([])
const sessionsLoading = ref(true)

// ─── 加载会话列表 ───
async function loadSessions() {
  try {
    const res = await listSessionsApi()
    // 后端 Result.ok() 包装了 Agent 的 { code, message, data: [...] }
    // 实际数组在 res.data.data 中
    const agentData = (res as any)?.data
    const list = agentData?.data ?? (res as any)?.data ?? []
    sessions.value = Array.isArray(list) ? list : []
  } catch {
    // ignore
  } finally {
    sessionsLoading.value = false
  }
}

// ─── 加载历史消息 ───
async function loadHistory(sid: string) {
  loading.value = true
  messages.value.length = 0
  try {
    const res = await fetchHistoryApi(sid)
    // 后端 Result.ok() 包装了 Agent 的 { code, message, data: { history } }
    const fastapiData = (res as any)?.data
    const innerData = fastapiData?.data ?? fastapiData
    const history = innerData?.history ?? []
    if (history.length > 0) {
      messages.value = history.map((m: any) => ({
        role: m.role as 'user' | 'assistant',
        content: m.content,
      }))
    } else {
      messages.value.push({
        role: 'assistant',
        content: '你好！我是 AI 助手，可以回答关于博客文章内容的问题。请问有什么可以帮助你的？',
      })
    }
  } catch {
    messages.value.push({
      role: 'assistant',
      content: '你好！我是 AI 助手，可以回答关于博客文章内容的问题。请问有什么可以帮助你的？',
    })
  } finally {
    loading.value = false
  }
}

// ─── 切换会话 ───
async function switchSession(sid: string) {
  if (sid === sessionId.value) return
  sessionId.value = sid
  saveSessionId(sid)
  await loadHistory(sid)
}

// ─── 新建会话 ───
function createNewSession() {
  const sid = `session-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
  saveSessionId(sid)
  sessionId.value = sid
  messages.value.length = 0
  messages.value.push({
    role: 'assistant',
    content: '你好！我是 AI 助手，可以回答关于博客文章内容的问题。请问有什么可以帮助你的？',
  })
  // 将新会话插入列表顶部
  sessions.value.unshift({
    session_id: sid,
    title: '新会话',
    message_count: 0,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  })
}

// ─── 删除会话 ───
async function deleteSession(sid: string) {
  try {
    await ElMessageBox.confirm('确定要删除该会话吗？', '删除会话', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await deleteSessionApi(sid)
  } catch {
    ElMessage.error('删除失败')
    return
  }
  sessions.value = sessions.value.filter(s => s.session_id !== sid)
  if (sid === sessionId.value) {
    // 切换到最近会话或新建
    if (sessions.value.length > 0) {
      await switchSession(sessions.value[0].session_id)
    } else {
      createNewSession()
    }
  }
}

// ─── 初始化 ───
onMounted(async () => {
  await loadSessions()
  await loadHistory(sessionId.value)
})

// ─── 自动滚动 ───
async function scrollToBottom() {
  await nextTick()
  if (messageList.value) {
    messageList.value.scrollTop = messageList.value.scrollHeight
  }
}
watch(messages, scrollToBottom, { deep: true })

// ─── 工具调用管理 ───
function handleToolCall(event: ToolCallEvent) {
  if (event.status === 'start') {
    const existing = toolCalls.value.find(t => t.name === event.name && t.status === 'start')
    if (!existing) {
      toolCalls.value.push({ name: event.name, status: 'start' })
    }
  } else if (event.status === 'end') {
    const idx = toolCalls.value.findIndex(t => t.name === event.name && t.status === 'start')
    if (idx !== -1) {
      toolCalls.value[idx].status = 'end'
      toolCalls.value[idx].result = event.result
    }
    setTimeout(() => {
      toolCalls.value = toolCalls.value.filter(t => t.status === 'start')
    }, 1500)
  }
}

function describeTool(name: string): string {
  const map: Record<string, string> = {
    retrieve_knowledge: '检索知识库',
    get_current_time: '获取当前时间',
  }
  return map[name] || name
}

// ─── 发送消息 ───
async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || sending.value) return

  inputText.value = ''
  messages.value.push({ role: 'user', content: text })

  const assistantMsg: ChatMessage = { role: 'assistant', content: '' }
  messages.value.push(assistantMsg)

  sending.value = true
  streaming.value = true

  try {
    const gen = streamChatApi(text, sessionId.value)
    let fullContent = ''
    let hasStreamed = false

    for await (const event of gen) {
      hasStreamed = true

      if (event.type === 'content') {
        fullContent += event.data
        assistantMsg.content = fullContent
        scrollToBottom()
      } else if (event.type === 'tool_call') {
        handleToolCall(event.data as ToolCallEvent)
      } else if (event.type === 'done') {
        break
      } else if (event.type === 'error') {
        assistantMsg.content = `抱歉，发生了错误：${event.data || '未知错误'}`
        return
      }
    }

    if (!hasStreamed) {
      assistantMsg.content = '（正在思考...）'
      const res = await chatApi(text, sessionId.value)
      const chatData = (res as any)?.data?.data
      if (chatData?.success && chatData?.answer) {
        assistantMsg.content = chatData.answer
      } else {
        assistantMsg.content = chatData?.errorMessage || '抱歉，我没有理解你的问题。'
      }
    }

    if (!assistantMsg.content) {
      assistantMsg.content = '（未获取到回答）'
    }
  } catch (e: any) {
    const idx = messages.value.indexOf(assistantMsg)
    if (idx !== -1) {
      messages.value[idx] = {
        role: 'assistant',
        content: `连接失败：${e.message}。请确认 Agent 服务已启动。`,
      }
    }
  } finally {
    sending.value = false
    streaming.value = false
    toolCalls.value = []
    // 刷新会话列表（更新标题、消息数、排序）
    await loadSessions()
  }
}

// ─── 清空当前会话 ───
async function clearSession() {
  try {
    await clearSessionApi(sessionId.value)
  } catch {
    // ignore
  }
  // 从列表移除后重建
  sessions.value = sessions.value.filter(s => s.session_id !== sessionId.value)
  createNewSession()
}

// ─── 渲染 Markdown ───
function renderMarkdown(text: string): string {
  if (!text) return ''
  try {
    let html = marked.parse(text) as string
    // 给 <pre> 添加 data-language 属性，用于 CSS 显示语言标签
    html = html.replace(
      /<pre><code class="hljs language-(\w+)">/g,
      '<pre data-language="$1"><code class="hljs language-$1">'
    )
    return html
  } catch {
    return text
  }
}

// ─── 键盘发送 ───
function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

// ─── 格式化时间 ───
function formatTime(isoStr: string): string {
  if (!isoStr) return ''
  try {
    const d = new Date(isoStr)
    const month = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    const hour = String(d.getHours()).padStart(2, '0')
    const min = String(d.getMinutes()).padStart(2, '0')
    return `${month}-${day} ${hour}:${min}`
  } catch {
    return ''
  }
}
</script>

<template>
  <div class="flex max-w-6xl mx-auto px-4 py-6 gap-4 h-[calc(100vh-8rem)]">
    <!-- ═══ 左侧：历史问答 ═══ -->
    <div class="w-64 flex-shrink-0 flex flex-col bg-white rounded-xl border border-gray-100 shadow-sm">
      <!-- 标题 -->
      <div class="px-3 py-3 border-b border-gray-100">
        <h2 class="text-sm font-semibold text-gray-700 flex items-center gap-1.5">
          <el-icon size="14"><Clock /></el-icon>
          历史问答
        </h2>
      </div>

      <!-- 会话列表 -->
      <div class="flex-1 overflow-y-auto">
        <div v-if="sessionsLoading" class="p-4 text-center text-xs text-gray-400">
          加载中...
        </div>
        <div v-else-if="sessions.length === 0" class="p-4 text-center text-xs text-gray-400">
          暂无历史会话
        </div>
        <template v-else>
          <div
            v-for="s in sessions"
            :key="s.session_id"
            class="group relative px-3 py-2.5 cursor-pointer border-b border-gray-50 hover:bg-gray-50 transition-colors"
            :class="s.session_id === sessionId ? 'bg-indigo-50 border-l-2 border-l-indigo-500 hover:bg-indigo-50' : 'border-l-2 border-l-transparent'"
            @click="switchSession(s.session_id)"
          >
            <div class="text-sm text-gray-700 truncate pr-6">{{ s.title }}</div>
            <div class="flex items-center gap-2 mt-0.5">
              <span class="text-xs text-gray-400">{{ s.message_count }} 条消息</span>
              <span v-if="s.updated_at" class="text-xs text-gray-400">{{ formatTime(s.updated_at) }}</span>
            </div>
            <!-- 删除按钮（hover 显示） -->
            <el-button
              class="!absolute right-1 top-1/2 -translate-y-1/2 !hidden group-hover:!inline-flex"
              size="small"
              circle
              text
              type="danger"
              @click.stop="deleteSession(s.session_id)"
            >
              <el-icon size="12"><Delete /></el-icon>
            </el-button>
          </div>
        </template>
      </div>

      <!-- 新建会话 -->
      <div class="p-3 border-t border-gray-100">
        <el-button size="small" class="!w-full" @click="createNewSession">
          <el-icon><Plus /></el-icon> 新对话
        </el-button>
      </div>
    </div>

    <!-- ═══ 右侧：对话区 ═══ -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Header -->
      <div class="flex items-center justify-between mb-4">
        <div>
          <h1 class="text-xl font-bold text-gray-800">AI 问答</h1>
          <p class="text-xs text-gray-400 mt-0.5">基于 RAG 知识库，回答博客相关内容</p>
        </div>
        <el-button size="small" plain @click="clearSession" :disabled="sending">
          <el-icon><Delete /></el-icon>
          清空会话
        </el-button>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex-1 flex items-center justify-center">
        <div class="text-center">
          <el-icon class="text-2xl text-gray-300 animate-spin"><Loading /></el-icon>
          <p class="mt-2 text-sm text-gray-400">加载历史消息...</p>
        </div>
      </div>

      <!-- Messages -->
      <div v-else ref="messageList" class="flex-1 overflow-y-auto space-y-4 pr-2">
        <!-- Tool call indicators -->
        <div v-if="toolCalls.length > 0" class="flex justify-start">
          <div class="flex items-start gap-2 max-w-[80%]">
            <div class="w-8 h-8 rounded-full bg-amber-50 text-amber-500 flex items-center justify-center text-sm font-medium flex-shrink-0">
              <el-icon><Tools /></el-icon>
            </div>
            <div class="bg-amber-50 border border-amber-100 text-amber-700 rounded-2xl rounded-tl-md px-4 py-2.5 shadow-sm">
              <div class="space-y-1">
                <div v-for="tc in toolCalls" :key="tc.name" class="flex items-center gap-2 text-sm">
                  <span v-if="tc.status === 'start'" class="w-2 h-2 bg-amber-400 rounded-full animate-pulse" />
                  <span v-else class="w-2 h-2 bg-green-400 rounded-full" />
                  <span>{{ describeTool(tc.name) }}</span>
                  <span v-if="tc.status === 'start'" class="text-xs text-amber-400 animate-pulse">进行中...</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Message bubbles -->
        <div
          v-for="(msg, i) in messages"
          :key="i"
          :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']"
        >
          <div :class="[msg.role === 'user' ? 'flex-row-reverse' : 'flex-row', 'flex items-start gap-2 max-w-[80%]']">
            <!-- Avatar -->
            <div
              :class="[
                msg.role === 'user'
                  ? 'bg-indigo-500 text-white'
                  : 'bg-gray-100 text-gray-500',
                'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium flex-shrink-0',
              ]"
            >
              {{ msg.role === 'user' ? 'U' : 'AI' }}
            </div>

            <!-- Bubble -->
            <div
              :class="[
                msg.role === 'user'
                  ? 'bg-indigo-500 text-white rounded-2xl rounded-tr-md'
                  : 'bg-white border border-gray-100 text-gray-700 rounded-2xl rounded-tl-md',
                'px-4 py-2.5 shadow-sm',
              ]"
            >
              <!-- Streaming waiting indicator -->
              <div v-if="msg.role === 'assistant' && !msg.content && streaming" class="flex items-center gap-1">
                <span class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
                <span class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
                <span class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
              </div>

              <!-- User: plain text -->
              <div v-else-if="msg.role === 'user'" class="text-sm leading-relaxed whitespace-pre-wrap">
                {{ msg.content }}
              </div>

              <!-- Assistant: markdown + streaming cursor -->
              <div v-else class="flex flex-wrap items-start gap-0">
                <div
                  class="markdown-body text-sm leading-relaxed"
                  v-html="renderMarkdown(msg.content)"
                />
                <span
                  v-if="streaming && messages[messages.length-1] === msg"
                  class="inline-block w-[3px] h-[1em] bg-indigo-500 rounded-sm animate-pulse ml-0.5 mt-[3px]"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Input -->
      <div class="mt-4 pt-4 border-t border-gray-100">
        <div class="flex items-end gap-2 bg-gray-50 rounded-2xl px-4 py-3 border border-gray-100 focus-within:border-indigo-300 focus-within:ring-2 focus-within:ring-indigo-100 transition-all">
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="1"
            :disabled="sending"
            placeholder="输入你的问题..."
            :autosize="{ minRows: 1, maxRows: 4 }"
            resize="none"
            class="flex-1 !border-none !shadow-none"
            @keydown="onKeydown"
          />
          <el-button
            type="primary"
            :icon="Promotion"
            :loading="sending"
            :disabled="!inputText.trim() || sending"
            circle
            @click="sendMessage"
          />
        </div>
        <p class="text-xs text-gray-400 mt-2 text-center">
          Enter 发送 · Shift+Enter 换行 · 基于 DeepSeek + RAG 知识库
        </p>
      </div>
    </div>
  </div>
</template>
