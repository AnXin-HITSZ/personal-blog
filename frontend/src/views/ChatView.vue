<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
    <nav class="bg-white shadow-lg border-b border-gray-200 sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex items-center">
            <h1 class="text-2xl font-bold text-gray-900 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Personal Blog
            </h1>
          </div>
          <div class="flex items-center space-x-2">
            <router-link
              to="/"
              exact-active-class="bg-blue-100 text-blue-700 border-blue-300 shadow-sm"
              class="text-gray-700 hover:text-gray-900 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 hover:bg-gray-100 border border-transparent"
            >
              Home
            </router-link>
            <router-link
              to="/chat"
              exact-active-class="bg-blue-100 text-blue-700 border-blue-300 shadow-sm"
              class="text-gray-700 hover:text-gray-900 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 hover:bg-gray-100 border border-transparent"
            >
              AI Chat
            </router-link>
            <router-link
              to="/profile"
              exact-active-class="bg-blue-100 text-blue-700 border-blue-300 shadow-sm"
              class="text-gray-700 hover:text-gray-900 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 hover:bg-gray-100 border border-transparent"
            >
              Profile
            </router-link>
            <el-button type="primary" @click="handleLogout" class="ml-4 shadow-md hover:shadow-lg transition-shadow">
              Logout
            </el-button>
          </div>
        </div>
      </div>
    </nav>

    <main class="max-w-5xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <div class="text-center mb-8">
        <h2 class="text-3xl font-extrabold text-gray-900 sm:text-4xl">
          AI Assistant
        </h2>
        <p class="mt-2 text-lg text-gray-600">
          Ask me anything about your blog or just have a conversation
        </p>
      </div>

      <!-- Chat Container -->
      <div class="bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-200">
        <!-- Model Selector -->
        <div class="border-b border-gray-200 px-6 py-4 bg-gradient-to-r from-gray-50 to-white">
          <div class="flex items-center space-x-4">
            <span class="text-sm font-semibold text-gray-500 tracking-wide uppercase">Agent:</span>
            <div class="flex bg-gray-100/80 rounded-xl p-1 gap-1">
              <!-- SimpleAgent -->
              <button
                @click="agentType = 'simple'"
                :class="[
                  'flex items-center gap-2.5 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200',
                  agentType === 'simple'
                    ? 'bg-white text-blue-700 shadow-sm border border-blue-200'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50 border border-transparent'
                ]"
              >
                <svg :class="agentType === 'simple' ? 'text-blue-500' : 'text-gray-400'" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
                <div class="text-left">
                  <div :class="agentType === 'simple' ? 'text-blue-700' : 'text-gray-700'" class="font-semibold leading-tight">SimpleAgent</div>
                  <div :class="agentType === 'simple' ? 'text-blue-400' : 'text-gray-400'" class="text-[11px] leading-tight mt-0.5">日常对话</div>
                </div>
                <div v-if="agentType === 'simple'" class="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"></div>
              </button>

              <!-- ReActAgent -->
              <button
                @click="agentType = 'react'"
                :class="[
                  'flex items-center gap-2.5 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200',
                  agentType === 'react'
                    ? 'bg-white text-purple-700 shadow-sm border border-purple-200'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50 border border-transparent'
                ]"
              >
                <svg :class="agentType === 'react' ? 'text-purple-500' : 'text-gray-400'" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                <div class="text-left">
                  <div :class="agentType === 'react' ? 'text-purple-700' : 'text-gray-700'" class="font-semibold leading-tight">ReActAgent</div>
                  <div :class="agentType === 'react' ? 'text-purple-400' : 'text-gray-400'" class="text-[11px] leading-tight mt-0.5">思维链模式</div>
                </div>
                <div v-if="agentType === 'react'" class="w-1.5 h-1.5 rounded-full bg-purple-500 animate-pulse"></div>
              </button>
            </div>
          </div>
        </div>

        <!-- Messages Area -->
        <div ref="messagesContainer" class="h-[500px] overflow-y-auto p-6 space-y-6">
          <div v-for="(message, index) in messages" :key="index">
            <!-- User message -->
            <div v-if="message.role === 'user'" class="flex justify-end mb-4">
              <div class="max-w-[80%] rounded-2xl px-5 py-3 bg-blue-600 text-white rounded-br-none">
                <div class="font-medium mb-1">You</div>
                <div class="whitespace-pre-wrap break-words">{{ message.content }}</div>
                <div class="text-xs opacity-70 mt-2 text-right">{{ message.timestamp }}</div>
              </div>
            </div>

            <!-- SimpleAgent assistant message -->
            <div v-else-if="message.role === 'assistant' && !message.reactData" class="flex justify-start mb-4">
              <div class="max-w-[80%] rounded-2xl px-5 py-3 bg-gray-100 text-gray-800 rounded-bl-none">
                <div class="font-medium mb-1">AI Assistant</div>

                <!-- Memory Context -->
                <div v-if="message.memories && message.memories.length > 0" class="mb-3">
                  <button
                    @click="message.memoriesCollapsed = !message.memoriesCollapsed"
                    class="flex items-center space-x-1.5 text-xs font-medium text-amber-600 hover:text-amber-700 transition-colors"
                  >
                    <svg
                      class="w-3 h-3 transition-transform duration-200"
                      :class="{ 'rotate-90': !message.memoriesCollapsed }"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
                    </svg>
                    <span>Memory Context ({{ message.memories.length }})</span>
                  </button>
                  <div v-show="!message.memoriesCollapsed" class="mt-2 space-y-1.5">
                    <div
                      v-for="(mem, mi) in message.memories"
                      :key="mi"
                      class="flex items-start gap-2 text-xs bg-amber-50/80 rounded-lg px-3 py-1.5 border border-amber-100"
                    >
                      <span class="text-gray-400 shrink-0 w-10 font-mono">{{ mem.timestamp }}</span>
                      <span
                        class="shrink-0 font-semibold px-1.5 py-0.5 rounded text-[10px] leading-tight"
                        :class="mem.role === 'user' ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700'"
                      >{{ mem.role }}</span>
                      <span class="text-gray-600 truncate">{{ mem.content }}</span>
                    </div>
                  </div>
                </div>

                <div class="markdown-body">
                  <div v-html="renderMarkdown(message.content)"></div>
                  <span v-if="message.streaming" class="inline-block w-2 h-4 ml-1 bg-gray-400 animate-pulse"></span>
                </div>
                <div class="text-xs opacity-70 mt-2 text-right">{{ message.timestamp }}</div>
              </div>
            </div>

            <!-- ReActAgent message -->
            <div v-else-if="message.role === 'assistant' && message.reactData" class="flex justify-start mb-4">
              <div class="max-w-[85%] rounded-2xl px-5 py-3 bg-gray-100 text-gray-800 rounded-bl-none">
                <div class="font-medium mb-1 text-purple-700">AI Assistant (ReAct)</div>

                <!-- Memory Context -->
                <div v-if="message.memories && message.memories.length > 0" class="mb-3">
                  <button
                    @click="message.memoriesCollapsed = !message.memoriesCollapsed"
                    class="flex items-center space-x-1.5 text-xs font-medium text-amber-600 hover:text-amber-700 transition-colors"
                  >
                    <svg
                      class="w-3 h-3 transition-transform duration-200"
                      :class="{ 'rotate-90': !message.memoriesCollapsed }"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
                    </svg>
                    <span>Memory Context ({{ message.memories.length }})</span>
                  </button>
                  <div v-show="!message.memoriesCollapsed" class="mt-2 space-y-1.5">
                    <div
                      v-for="(mem, mi) in message.memories"
                      :key="mi"
                      class="flex items-start gap-2 text-xs bg-amber-50/80 rounded-lg px-3 py-1.5 border border-amber-100"
                    >
                      <span class="text-gray-400 shrink-0 w-10 font-mono">{{ mem.timestamp }}</span>
                      <span
                        class="shrink-0 font-semibold px-1.5 py-0.5 rounded text-[10px] leading-tight"
                        :class="mem.role === 'user' ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700'"
                      >{{ mem.role }}</span>
                      <span class="text-gray-600 truncate">{{ mem.content }}</span>
                    </div>
                  </div>
                </div>

                <!-- Collapsible ReAct Process -->
                <div v-if="message.reactData.steps.length > 0" class="mb-5">
                  <button
                    @click="toggleReactCollapse(index)"
                    class="flex items-center space-x-2 text-xs font-medium text-gray-500 hover:text-gray-700 transition-colors mb-2"
                  >
                    <svg
                      class="w-3 h-3 transition-transform duration-200"
                      :class="{ 'rotate-90': !message.reactCollapsed }"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
                    </svg>
                    <span>ReAct Process ({{ message.reactData.steps.length }} steps)</span>
                    <span v-if="message.streaming" class="w-2 h-2 bg-purple-500 rounded-full animate-pulse"></span>
                  </button>

                  <div v-show="!message.reactCollapsed" class="space-y-2">
                    <div
                      v-for="(step, si) in message.reactData.steps"
                      :key="si"
                      class="border border-gray-200 rounded-lg overflow-hidden"
                    >
                      <!-- Step header -->
                      <div class="bg-gray-50 px-3 py-1.5 text-xs font-medium text-gray-500 border-b border-gray-200">
                        Step {{ step.stepNumber }}
                      </div>

                      <!-- Thought -->
                      <div v-if="step.thought" class="px-3 py-2 bg-amber-50 border-b border-gray-200">
                        <div class="flex">
                          <span class="text-xs font-semibold text-amber-700 w-24 shrink-0">Thought:</span>
                          <span class="text-sm text-gray-700 whitespace-pre-wrap">{{ step.thought }}</span>
                        </div>
                      </div>

                      <!-- Action -->
                      <div v-if="step.action" class="px-3 py-2 bg-blue-50 border-b border-gray-200">
                        <div class="flex">
                          <span class="text-xs font-semibold text-blue-700 w-24 shrink-0">Action:</span>
                          <span class="text-sm text-gray-700 whitespace-pre-wrap font-mono">
                            {{ step.action.tool }}({{ step.action.input }})
                          </span>
                        </div>
                      </div>

                      <!-- Observation -->
                      <div v-if="step.observation" class="px-3 py-2 bg-green-50 border-b border-gray-200">
                        <div class="flex">
                          <span class="text-xs font-semibold text-green-700 w-24 shrink-0">Observation:</span>
                          <span class="text-sm text-gray-700 whitespace-pre-wrap">{{ step.observation }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Final Answer -->
                <div class="markdown-body">
                  <div v-html="renderMarkdown(message.content)"></div>
                  <span v-if="message.streaming" class="inline-block w-2 h-4 ml-1 bg-gray-400 animate-pulse"></span>
                </div>
                <div class="text-xs opacity-70 mt-2 text-right">{{ message.timestamp }}</div>
              </div>
            </div>
          </div>

          <!-- Empty state -->
          <div v-if="messages.length === 0" class="text-center py-12 text-gray-500">
            <div class="text-5xl mb-4">🤖</div>
            <p class="text-xl">Start a conversation with the AI assistant</p>
            <p class="mt-2">Try asking about blog writing tips or anything else!</p>
          </div>
        </div>

        <!-- Input Area -->
        <div class="border-t border-gray-200 p-4 bg-gray-50">
          <div class="flex space-x-3">
            <el-input
              v-model="inputMessage"
              type="textarea"
              :rows="2"
              placeholder="Type your message here..."
              :disabled="loading"
              @keydown.enter.exact.prevent="handleSendMessage"
              class="flex-grow"
              resize="none"
            />
            <el-button
              type="primary"
              :loading="loading"
              :disabled="!inputMessage.trim() || loading"
              @click="handleSendMessage"
              class="self-end px-6"
              size="large"
            >
              Send
            </el-button>
          </div>
          <div class="mt-3 flex justify-end items-center text-sm text-gray-500">
            <el-button type="info" plain @click="handleClearChat" size="small">Clear Chat</el-button>
          </div>
        </div>
      </div>

      <!-- Tips Section -->
      <div class="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
          <h3 class="font-bold text-lg text-gray-900 mb-2">💡 Writing Tips</h3>
          <p class="text-gray-600">Ask for advice on improving your blog posts, structuring articles, or engaging readers.</p>
        </div>
        <div class="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
          <h3 class="font-bold text-lg text-gray-900 mb-2">🔍 Research</h3>
          <p class="text-gray-600">Get help with research for your next article topic or find relevant sources.</p>
        </div>
        <div class="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
          <h3 class="font-bold text-lg text-gray-900 mb-2">✏️ Editing</h3>
          <p class="text-gray-600">Request grammar checks, style improvements, or readability analysis.</p>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { streamSimpleAgentChat, streamReActAgentChat } from '@/api/agent'
import type { ChatMessage, ChatRequest, AgentType, ReActData, MemoryItem } from '@/types/api'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
})

const renderMarkdown = (text: string): string => {
  if (!text) return ''
  return md.render(text)
}
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

interface Message {
  role: string
  content: string
  timestamp: string
  streaming?: boolean
  memories?: MemoryItem[]
  memoriesCollapsed?: boolean
  reactData?: ReActData
  reactCollapsed?: boolean
}

const messages = ref<Message[]>([])
const inputMessage = ref('')
const loading = ref(false)
const agentType = ref<AgentType>('simple')
const messagesContainer = ref<HTMLElement>()
const sessionId = ref<string>('')

let abortStream: (() => void) | null = null

const formatTime = (date: Date) => {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const addMessage = (role: string, content: string, streaming = false) => {
  const timestamp = formatTime(new Date())
  const message: Message = { role, content, timestamp, streaming }
  messages.value.push(message)
  scrollToBottom()
}

const toggleReactCollapse = (index: number) => {
  const msg = messages.value[index]
  if (msg) {
    msg.reactCollapsed = !msg.reactCollapsed
  }
}

const handleSendMessage = async () => {
  if (abortStream) {
    abortStream()
    abortStream = null
  }

  const text = inputMessage.value.trim()
  if (!text || loading.value) return

  loading.value = true

  // Add user message
  addMessage('user', text)
  inputMessage.value = ''

  // Add placeholder assistant message
  addMessage('assistant', '', true)
  const msgIndex = messages.value.length - 1

  // Initialize reactData for ReAct agent
  if (agentType.value === 'react') {
    messages.value[msgIndex].reactData = { steps: [], finalAnswer: '' }
    messages.value[msgIndex].reactCollapsed = false
  }

  // 过滤掉内容为空的消息（避免发送占位符消息给后端），并传入时间戳
  const filteredMessages: ChatMessage[] = messages.value
    .filter(m => m.content.trim() !== '')
    .map(m => ({ role: m.role, content: m.content, timestamp: Date.now() }))

  const request: ChatRequest = {
    sessionId: sessionId.value,
    messages: filteredMessages,
  }

  if (agentType.value === 'simple') {
    abortStream = streamSimpleAgentChat(
      request,
      (chunk) => {
        const lastMsg = messages.value[msgIndex]
        if (lastMsg) {
          lastMsg.content += chunk
          lastMsg.streaming = true
          scrollToBottom()
        }
      },
      (memories) => {
        const lastMsg = messages.value[msgIndex]
        if (lastMsg) {
          // 后端返回的是 Tuple 格式 [score, {role, content, time}]，转换为对象
          lastMsg.memories = (memories || []).map((item: any) => ({
            timestamp: item[1]?.time || '',
            role: item[1]?.role || '',
            content: item[1]?.content || ''
          }))
          lastMsg.memoriesCollapsed = true
        }
      },
      (error) => {
        console.error('SimpleAgent stream error:', error)
        ElMessage.error('Failed to get response')
        const lastMsg = messages.value[msgIndex]
        if (lastMsg) {
          lastMsg.streaming = false
          if (lastMsg.content === '') {
            lastMsg.content = 'Sorry, an error occurred.'
          }
        }
        loading.value = false
      },
      () => {
        const lastMsg = messages.value[msgIndex]
        if (lastMsg) {
          lastMsg.streaming = false
        }
        loading.value = false
        abortStream = null
      }
    )
  } else {
    let pendingStepNumber: number | null = null
    abortStream = streamReActAgentChat(
      request,
      (event) => {
        const lastMsg = messages.value[msgIndex]
        if (!lastMsg) return

        const { type, data } = event

        // memory 事件不依赖 reactData，需要优先处理
        if (type === 'memory') {
          const memories = (data || []).map((item: any) => ({
            timestamp: item[1]?.time || '',
            role: item[1]?.role || '',
            content: item[1]?.content || ''
          }))
          lastMsg.memories = memories
          lastMsg.memoriesCollapsed = true
          return
        }

        if (!lastMsg.reactData) return

        // 缓存 step 事件，等收到非错误事件时再真正推入数组，避免推入又弹出导致页面抖动
        if (type === 'step') {
          pendingStepNumber = data
          return
        }

        // 错误事件：丢弃缓存的 step，不触发任何渲染
        if (type === 'error') {
          pendingStepNumber = null
          return
        }

        // 真实内容事件：先提交缓存的 step，再处理数据
        if (pendingStepNumber !== null) {
          lastMsg.reactData.steps.push({ stepNumber: pendingStepNumber })
          pendingStepNumber = null
        }

        if (type === 'thought') {
          const steps = lastMsg.reactData.steps
          if (steps.length > 0) {
            steps[steps.length - 1].thought = data
          }
        } else if (type === 'action') {
          const steps = lastMsg.reactData.steps
          if (steps.length > 0) {
            steps[steps.length - 1].action = data
          }
        } else if (type === 'observation') {
          const steps = lastMsg.reactData.steps
          if (steps.length > 0) {
            steps[steps.length - 1].observation = data
          }
        } else if (type === 'final_answer') {
          lastMsg.reactData.finalAnswer = data
          lastMsg.content = data
        }

        scrollToBottom()
      },
      (error) => {
        console.error('ReActAgent stream error:', error)
        ElMessage.error('Failed to get response')
        const lastMsg = messages.value[msgIndex]
        if (lastMsg) {
          lastMsg.streaming = false
          if (lastMsg.content === '') {
            lastMsg.content = 'Sorry, an error occurred.'
          }
        }
        loading.value = false
      },
      () => {
        const lastMsg = messages.value[msgIndex]
        if (lastMsg) {
          lastMsg.streaming = false
        }
        loading.value = false
        abortStream = null
      }
    )
  }
}

const handleClearChat = () => {
  if (abortStream) {
    abortStream()
    abortStream = null
  }
  messages.value = []
  loading.value = false
}

const handleLogout = () => {
  localStorage.removeItem('token')
  ElMessage.success('Logged out successfully')
  router.push('/login')
}

onMounted(() => {
  const userId = authStore.userInfo?.userId || 'anonymous'
  const timestamp = Date.now()
  const random = Math.random().toString(36).substring(2, 9)
  sessionId.value = `session-${userId}-${timestamp}-${random}`
})
</script>

<style scoped>
::-webkit-scrollbar {
  width: 8px;
}
::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}
::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: #a1a1a1;
}

.markdown-body :deep(p) {
  margin-bottom: 0.5rem;
}

.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 1.5rem;
  margin-bottom: 0.5rem;
}

.markdown-body :deep(li) {
  margin-bottom: 0.25rem;
}

.markdown-body :deep(code) {
  background-color: #f3f4f6;
  padding: 0.15rem 0.35rem;
  border-radius: 4px;
  font-size: 0.875em;
  font-family: 'Courier New', Courier, monospace;
}

.markdown-body :deep(pre) {
  background-color: #f8f9fa;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1rem;
  overflow-x: auto;
  margin-bottom: 0.75rem;
}

.markdown-body :deep(pre code) {
  background: none;
  padding: 0;
  font-size: 0.8rem;
  line-height: 1.5;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4) {
  font-weight: 600;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
}

.markdown-body :deep(h1) { font-size: 1.25rem; }
.markdown-body :deep(h2) { font-size: 1.125rem; }
.markdown-body :deep(h3) { font-size: 1rem; }

.markdown-body :deep(blockquote) {
  border-left: 3px solid #d1d5db;
  padding-left: 0.75rem;
  margin: 0.5rem 0;
  color: #6b7280;
}

.markdown-body :deep(a) {
  color: #2563eb;
  text-decoration: underline;
}

.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid #e5e7eb;
  margin: 0.75rem 0;
}

.markdown-body :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin-bottom: 0.75rem;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid #e5e7eb;
  padding: 0.4rem 0.6rem;
  text-align: left;
  font-size: 0.875rem;
}

.markdown-body :deep(th) {
  background-color: #f9fafb;
  font-weight: 600;
}

.markdown-body :deep(strong) {
  font-weight: 600;
}
</style>
