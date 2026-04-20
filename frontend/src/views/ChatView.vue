<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
    <nav class="bg-white shadow-sm border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex items-center">
            <h1 class="text-2xl font-bold text-gray-900">Personal Blog</h1>
          </div>
          <div class="flex items-center space-x-4">
            <router-link to="/" class="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
              Home
            </router-link>
            <router-link to="/chat" class="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium bg-blue-50">
              AI Chat
            </router-link>
            <router-link to="/profile" class="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
              Profile
            </router-link>
            <el-button type="primary" @click="handleLogout" class="ml-4">
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
        <!-- Messages Area -->
        <div ref="messagesContainer" class="h-[500px] overflow-y-auto p-6 space-y-6">
          <div v-for="(message, index) in messages" :key="index" class="flex" :class="message.role === 'user' ? 'justify-end' : 'justify-start'">
            <div
              class="max-w-[80%] rounded-2xl px-5 py-3"
              :class="message.role === 'user' ? 'bg-blue-600 text-white rounded-br-none' : 'bg-gray-100 text-gray-800 rounded-bl-none'"
            >
              <div class="font-medium mb-1">
                {{ message.role === 'user' ? 'You' : 'AI' }}
              </div>
              <div class="whitespace-pre-wrap break-words">
                {{ message.content }}
                <span v-if="message.streaming && message.role === 'assistant'" class="inline-block w-2 h-4 ml-1 bg-gray-400 animate-pulse"></span>
              </div>
              <div class="text-xs opacity-70 mt-2 text-right">
                {{ message.timestamp }}
              </div>
            </div>
          </div>

          <!-- Loading indicator when waiting for response -->
          <div v-if="loading" class="flex justify-start">
            <div class="max-w-[80%] rounded-2xl rounded-bl-none bg-gray-100 text-gray-800 px-5 py-3">
              <div class="font-medium mb-1">AI</div>
              <div class="flex items-center space-x-2">
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.4s"></div>
              </div>
            </div>
          </div>

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
          <div class="mt-3 flex justify-between items-center text-sm text-gray-500">
            <div>
              <el-checkbox v-model="enableStream" label="Stream response" />
              <span class="ml-2">Temperature: </span>
              <el-slider v-model="temperature" :min="0" :max="1" :step="0.1" :show-tooltip="true" style="width: 120px; display: inline-block; margin-left: 8px;" />
              <span class="ml-2">{{ temperature.toFixed(1) }}</span>
            </div>
            <div>
              <el-button type="info" plain @click="handleClearChat" size="small">Clear Chat</el-button>
            </div>
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
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { streamChat, chat } from '@/api/agent'
import type { ChatMessage, ChatRequest } from '@/types/api'

const router = useRouter()

interface Message extends ChatMessage {
  timestamp: string
  streaming?: boolean
}

const messages = ref<Message[]>([])
const inputMessage = ref('')
const loading = ref(false)
const enableStream = ref(true)
const temperature = ref(0.7)
const messagesContainer = ref<HTMLElement>()

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
  messages.value.push({ role, content, timestamp, streaming })
  scrollToBottom()
}

const updateLastMessage = (content: string) => {
  const last = messages.value[messages.value.length - 1]
  if (last && last.role === 'assistant') {
    last.content = content
    scrollToBottom()
  }
}

const handleSendMessage = async () => {
  // Abort previous stream if any
  if (abortStream) {
    abortStream()
    abortStream = null
  }
  const text = inputMessage.value.trim()
  if (!text || loading.value) return

  // Add user message
  addMessage('user', text)
  inputMessage.value = ''

  // Add placeholder assistant message
  if (enableStream.value) {
    addMessage('assistant', '', true)
  } else {
    loading.value = true
  }

  const request: ChatRequest = {
    messages: messages.value.map(m => ({ role: m.role, content: m.content })),
    temperature: temperature.value,
    isStream: enableStream.value,
  }

  if (enableStream.value) {
    // Stream response
    abortStream = streamChat(
      request,
      (chunk) => {
        const last = messages.value[messages.value.length - 1]
        if (last && last.role === 'assistant') {
          last.content += chunk
          last.streaming = true
          scrollToBottom()
        }
      },
      (error) => {
        console.error('Stream error:', error)
        ElMessage.error('Failed to get response')
        if (messages.value.length > 0 && messages.value[messages.value.length - 1].role === 'assistant') {
          messages.value[messages.value.length - 1].streaming = false
          if (messages.value[messages.value.length - 1].content === '') {
            messages.value[messages.value.length - 1].content = 'Sorry, an error occurred.'
          }
        }
        loading.value = false
      },
      () => {
        // Stream complete
        if (messages.value.length > 0 && messages.value[messages.value.length - 1].role === 'assistant') {
          messages.value[messages.value.length - 1].streaming = false
        }
        loading.value = false
        abortStream = null
      }
    )
  } else {
    // Non‑stream response
    try {
      const response = await chat(request)
      addMessage('assistant', response.content)
    } catch (error) {
      console.error('Chat error:', error)
      ElMessage.error('Failed to get response')
    } finally {
      loading.value = false
    }
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

// Auto‑focus input on mount
onMounted(() => {
  // Optional: load previous messages from localStorage?
})
</script>

<style scoped>
/* Custom scrollbar */
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
</style>