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

    <main class="max-w-[1600px] mx-auto py-6 px-4 sm:px-6 lg:px-8 h-[calc(100vh-4rem)]">
      <div class="flex gap-5 h-full">
        <!-- History Sidebar -->
        <aside class="w-[420px] shrink-0">
          <div class="bg-white rounded-2xl shadow-lg overflow-hidden border border-gray-200/80 h-full flex flex-col">
            <HistorySidebar
              :sessions="sessions"
              :active-session-id="sessionId"
              @select-session="handleSelectSession"
              @delete-session="handleDeleteSession"
              @rename-session="handleRenameSession"
              @new-chat="handleNewChat"
            />
          </div>
        </aside>

        <!-- Chat Area -->
        <div class="flex-1 min-w-0 flex flex-col h-full">
          <div class="text-center mb-3 flex-shrink-0">
            <h2 class="text-xl font-bold text-gray-900">
              AI Assistant
            </h2>
            <p class="mt-0.5 text-sm text-gray-400">
              Powered by ReAct Agent · Knowledge Base
            </p>
          </div>

          <!-- Chat Container -->
          <div class="bg-white rounded-2xl shadow-lg overflow-hidden border border-gray-200/80 flex flex-col flex-1 min-h-0">
        <!-- Agent Selector -->
        <div class="border-b border-gray-200/80 px-5 py-2.5 bg-white flex-shrink-0">
          <div class="flex items-center space-x-3">
            <span class="text-xs font-semibold text-gray-400 tracking-wider uppercase">Agent</span>
            <div class="flex bg-gray-50 rounded-lg p-0.5 gap-0.5">
              <!-- ReActAgent -->
              <div
                class="flex items-center gap-2 px-3.5 py-2 rounded-md text-sm font-medium bg-gradient-to-r from-purple-50 to-purple-100/80 text-purple-700 shadow-sm border border-purple-200/60"
              >
                <svg class="w-4 h-4 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                <div class="text-left">
                  <div class="text-purple-700 font-semibold leading-tight">ReActAgent</div>
                  <div class="text-purple-400 text-[11px] leading-tight mt-0.5">思维链模式 · 知识库检索</div>
                </div>
                <div class="w-1.5 h-1.5 rounded-full bg-purple-500 animate-pulse"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Messages Area -->
        <div ref="messagesContainer" class="flex-1 overflow-y-auto p-5 space-y-5 bg-[#fafbfc] min-h-0">
          <div v-for="(message, index) in messages" :key="index" class="animate-fadeIn">
            <!-- User message -->
            <div v-if="message.role === 'user'" class="flex justify-end mb-3">
              <div class="max-w-[75%] rounded-2xl px-4 py-2.5 bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-br-sm shadow-sm">
                <div class="whitespace-pre-wrap break-words text-[15px] leading-relaxed">{{ message.content }}</div>
                <div class="text-[11px] text-blue-200 mt-1.5 text-right">{{ message.timestamp }}</div>
              </div>
            </div>

            <!-- ReActAgent message -->
            <div v-else-if="message.role === 'assistant' && message.reactData" class="flex justify-start mb-3">
              <div class="max-w-[85%] rounded-2xl px-4 py-2.5 bg-white text-gray-800 rounded-bl-sm shadow-sm border border-gray-100">
                <div class="flex items-center gap-1.5 mb-2">
                  <span class="w-5 h-5 rounded-full bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center">
                    <svg class="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                  </span>
                  <span class="text-xs font-semibold text-purple-600">AI Assistant</span>
                  <span v-if="message.streaming" class="w-1.5 h-1.5 rounded-full bg-purple-500 animate-pulse"></span>
                </div>

                <!-- Memory Context -->
                <div v-if="message.memories && message.memories.length > 0" class="mb-3">
                  <button
                    @click="message.memoriesCollapsed = !message.memoriesCollapsed"
                    class="flex items-center gap-1.5 text-xs font-medium text-amber-600 hover:text-amber-700 transition-colors"
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
                  <div v-show="!message.memoriesCollapsed" class="mt-2 space-y-1">
                    <div
                      v-for="(mem, mi) in message.memories"
                      :key="mi"
                      class="flex items-start gap-2 text-xs bg-amber-50/60 rounded-lg px-2.5 py-1.5 border border-amber-100/60"
                    >
                      <span class="text-gray-400 shrink-0 w-9 font-mono text-[10px]">{{ mem.timestamp }}</span>
                      <span
                        class="shrink-0 font-semibold px-1.5 py-0.5 rounded text-[10px] leading-tight"
                        :class="mem.role === 'user' ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700'"
                      >{{ mem.role }}</span>
                      <span class="text-gray-500 truncate">{{ mem.content }}</span>
                    </div>
                  </div>
                </div>

                <!-- Collapsible ReAct Process -->
                <div v-if="message.reactData.steps.length > 0" class="mb-4">
                  <button
                    @click="toggleReactCollapse(index)"
                    class="flex items-center gap-1.5 text-xs font-medium text-gray-400 hover:text-gray-600 transition-colors mb-2"
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
                    <span v-if="message.streaming" class="w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse"></span>
                  </button>

                  <div v-show="!message.reactCollapsed" class="space-y-1.5">
                    <div
                      v-for="(step, si) in message.reactData.steps"
                      :key="si"
                      class="border border-gray-100 rounded-lg overflow-hidden"
                    >
                      <!-- Step header -->
                      <div class="bg-gray-50/80 px-2.5 py-1 text-xs font-medium text-gray-400 border-b border-gray-100">
                        Step {{ step.stepNumber }}
                      </div>

                      <!-- Thought -->
                      <div v-if="step.thought" class="px-2.5 py-1.5 bg-amber-50/40 border-b border-gray-100">
                        <div class="flex gap-2">
                          <span class="text-[11px] font-semibold text-amber-600 shrink-0 w-16">Thought:</span>
                          <span class="text-[13px] text-gray-600 whitespace-pre-wrap">{{ step.thought }}</span>
                        </div>
                      </div>

                      <!-- Action -->
                      <div v-if="step.action" class="px-2.5 py-1.5 bg-blue-50/40 border-b border-gray-100">
                        <div class="flex gap-2">
                          <span class="text-[11px] font-semibold text-blue-600 shrink-0 w-16">Action:</span>
                          <span class="text-[13px] text-gray-600 whitespace-pre-wrap font-mono">
                            {{ step.action.tool }}({{ step.action.input }})
                          </span>
                        </div>
                      </div>

                      <!-- Observation -->
                      <div v-if="step.observation" class="px-2.5 py-1.5 bg-green-50/40">
                        <div class="flex gap-2">
                          <span class="text-[11px] font-semibold text-green-600 shrink-0 w-16">Observation:</span>
                          <span class="text-[13px] text-gray-600 whitespace-pre-wrap">{{ step.observation }}</span>
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

            <!-- Plain assistant message (历史对话，无 ReAct 数据) -->
            <div v-else-if="message.role === 'assistant'" class="flex justify-start mb-3">
              <div class="max-w-[85%] rounded-2xl px-4 py-2.5 bg-white text-gray-800 rounded-bl-sm shadow-sm border border-gray-100">
                <div class="flex items-center gap-1.5 mb-1.5">
                  <span class="w-5 h-5 rounded-full bg-gradient-to-br from-gray-400 to-gray-500 flex items-center justify-center">
                    <svg class="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                  </span>
                  <span class="text-xs font-semibold text-gray-500">AI Assistant</span>
                </div>
                <div class="markdown-body">
                  <div v-html="renderMarkdown(message.content)"></div>
                </div>
                <div class="text-[11px] text-gray-400 mt-1.5 text-right">{{ message.timestamp }}</div>
              </div>
            </div>
          </div>

          <!-- Empty state -->
          <div v-if="messages.length === 0" class="flex flex-col items-center justify-center py-16 text-gray-400 select-none">
            <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center mb-4 shadow-sm">
              <svg class="w-8 h-8 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <p class="text-base font-medium text-gray-500">Start a conversation</p>
            <p class="text-sm mt-1">Type a message below to begin chatting with AI</p>
          </div>
        </div>

        <!-- Input Area -->
        <div class="border-t border-gray-200/80 px-4 py-3 bg-white">
          <div class="flex items-end gap-3">
            <div class="flex-1 relative">
              <el-input
                v-model="inputMessage"
                type="textarea"
                :rows="2"
                placeholder="Type your message here..."
                :disabled="loading"
                @keydown.enter.exact.prevent="handleSendMessage"
                class="chat-input"
                resize="none"
              />
            </div>
            <el-button
              type="primary"
              :loading="loading"
              :disabled="!inputMessage.trim() || loading"
              @click="handleSendMessage"
              class="send-btn self-end"
              size="large"
              round
            >
              <svg v-if="!loading" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 19V5m0 0l-7 7m7-7l7 7" />
              </svg>
              <span v-else>Sending...</span>
            </el-button>
          </div>
          <div class="mt-2 flex justify-between items-center">
            <span class="text-xs text-gray-400">Press Enter to send</span>
            <el-button text bg size="small" @click="handleClearChat" class="text-gray-400 hover:text-gray-600">
              Clear conversation
            </el-button>
          </div>
        </div>
      </div>

        </div>

        <!-- Right Sidebar: Tab-switch between KB and Plan -->
        <aside class="w-72 shrink-0">
          <div class="bg-white rounded-2xl shadow-lg overflow-hidden border border-gray-200/80 h-full flex flex-col">
            <!-- Tab header -->
            <div class="flex border-b border-gray-200/80 bg-gray-50/50 flex-shrink-0">
              <button
                class="flex-1 px-3 py-2 text-xs font-semibold tracking-wider uppercase transition-colors relative"
                :class="rightTab === 'kb' ? 'text-blue-600 bg-white' : 'text-gray-400 hover:text-gray-600'"
                @click="rightTab = 'kb'"
              >
                知识库
                <div
                  v-if="rightTab === 'kb'"
                  class="absolute bottom-0 left-2 right-2 h-0.5 bg-blue-500 rounded-full"
                />
              </button>
              <button
                class="flex-1 px-3 py-2 text-xs font-semibold tracking-wider uppercase transition-colors relative"
                :class="rightTab === 'plan' ? 'text-purple-600 bg-white' : 'text-gray-400 hover:text-gray-600'"
                @click="rightTab = 'plan'"
              >
                计划
                <div
                  v-if="rightTab === 'plan'"
                  class="absolute bottom-0 left-2 right-2 h-0.5 bg-purple-500 rounded-full"
                />
              </button>
            </div>

            <!-- Knowledge Base Panel -->
            <div v-show="rightTab === 'kb'" class="flex-1 flex flex-col min-h-0">
              <div class="px-4 py-3 border-b border-gray-200/80 bg-white flex-shrink-0">
                <div class="flex items-center justify-between">
                  <h3 class="text-xs font-bold text-gray-400 tracking-wider uppercase">Knowledge Base</h3>
                  <el-button
                    v-if="isAdmin"
                    type="primary"
                    size="small"
                    @click="showAddDialogFn"
                    :icon="Plus"
                    circle
                  />
                </div>
              </div>
              <div class="flex-1 overflow-y-auto p-3 min-h-0">
                <div v-if="knowledgeBases.length === 0" class="text-center py-8 text-gray-400">
                  <svg class="w-10 h-10 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                  <p class="text-sm">暂无知识库</p>
                  <p v-if="isAdmin" class="text-xs mt-1">点击右上角 + 新增</p>
                </div>
                <div v-else class="space-y-2">
                  <div
                    v-for="kb in knowledgeBases"
                    :key="kb.ragId"
                    class="group rounded-lg border border-gray-200 hover:border-blue-300 transition-colors"
                  >
                    <div class="px-3 py-2.5">
                      <div class="flex items-start justify-between">
                        <div class="min-w-0 flex-1">
                          <div class="flex items-center gap-1.5">
                            <svg class="w-4 h-4 text-blue-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                              <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                            </svg>
                            <span class="text-sm font-medium text-gray-800 truncate">{{ kb.name }}</span>
                          </div>
                          <div class="flex items-center gap-2 mt-1">
                            <span class="text-[11px] text-gray-400">{{ kb.fileCount || 0 }} 文件</span>
                            <span
                              class="text-[11px] px-1.5 py-0.5 rounded-full"
                              :class="kb.status === 1 ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'"
                            >{{ kb.status === 1 ? '已索引' : '未索引' }}</span>
                          </div>
                          <p v-if="kb.description" class="text-xs text-gray-400 mt-1 truncate">{{ kb.description }}</p>
                        </div>
                        <div v-if="isAdmin" class="flex gap-1 shrink-0 ml-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <el-button size="small" :icon="Edit" circle @click="editKB(kb)" />
                          <el-button size="small" type="danger" :icon="Delete" circle @click="handleDeleteKB(kb)" />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Plan Panel -->
            <div v-show="rightTab === 'plan'" class="flex-1 min-h-0">
              <PlanPanel
                :plan="currentPlan"
                @delete="currentPlan = null"
              />
            </div>
          </div>
        </aside>
      </div>
    </main>

    <!-- Add/Edit Knowledge Base Dialog -->
    <el-dialog
      v-model="kbDialogVisible"
      :title="editingKB ? '编辑知识库' : '新增知识库'"
      width="480px"
      :close-on-click-modal="false"
    >
      <el-form :model="kbForm" label-width="80px" size="default">
        <el-form-item label="名称" required>
          <el-input v-model="kbForm.name" placeholder="知识库名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="kbForm.description" placeholder="简要描述" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="命名空间" required>
          <el-input v-model="kbForm.namespace" placeholder="唯一标识，如 my-knowledge" :disabled="!!editingKB" />
        </el-form-item>
        <el-form-item label="上传文件">
          <div class="flex items-center gap-2">
            <input
              ref="folderInputRef"
              type="file"
              webkitdirectory
              multiple
              hidden
              @change="handleFileSelect"
            />
            <input
              ref="fileInputRef"
              type="file"
              multiple
              hidden
              @change="handleFileSelect"
            />
            <el-button
              type="primary"
              size="small"
              :disabled="!!editingKB || uploadingFiles"
              @click="folderInputRef?.click()"
            >
              {{ uploadingFiles ? '上传中...' : '选择文件夹' }}
            </el-button>
            <el-button
              size="small"
              :disabled="!!editingKB || uploadingFiles"
              @click="fileInputRef?.click()"
            >
              {{ uploadingFiles ? '上传中...' : '选择文件' }}
            </el-button>
            <span v-if="indexingStatus === 'indexing'" class="text-sm text-blue-500">
              索引中...
            </span>
            <span v-else-if="indexingStatus === 'done'" class="text-sm text-green-600">
              索引完成，共 {{ uploadedFileCount }} 个文件
            </span>
            <span v-else-if="indexingStatus === 'failed'" class="text-sm text-red-500">
              索引失败
            </span>
            <span v-else-if="uploadedFileCount > 0" class="text-sm text-green-600">
              已上传 {{ uploadedFileCount }} 个文件
            </span>
            <span v-else class="text-sm text-gray-400">未选择</span>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="kbDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="kbSaving" @click="handleSaveKB" :disabled="!editingKB && indexingStatus !== 'done'">
          {{ editingKB ? '更新' : '保存' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- Delete Confirmation Dialog -->
    <el-dialog
      v-model="deleteDialogVisible"
      title="确认删除"
      width="360px"
    >
      <p>确定要删除知识库「{{ deletingKB?.name }}」吗？此操作不可撤销。</p>
      <template #footer>
        <el-button @click="deleteDialogVisible = false">取消</el-button>
        <el-button type="danger" :loading="kbSaving" @click="handleConfirmDelete">删除</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import { streamReActAgentChat } from '@/api/agent'
import { getRAGListApi, addRAGApi, updateRAGApi, deleteRAGApi, uploadRAGFilesApi } from '@/api/rag'
import { initSessionApi } from '@/api/session'
import { listSessionsApi, getSessionMessagesApi, deleteSessionApi, updateSessionTitleApi } from '@/api/history'
import { getPlanBySessionApi } from '@/api/plan'
import type { ChatRequest, ReActData, MemoryItem, RAGKnowledgeBase, SessionDTO, Plan, PlanEvent } from '@/types/api'
import HistorySidebar from '@/components/Chat/HistorySidebar.vue'
import PlanPanel from '@/components/Plan/PlanPanel.vue'
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
const messagesContainer = ref<HTMLElement>()
const sessionId = ref<string>('')

// History sidebar state
const sessions = ref<SessionDTO[]>([])
const sessionsLoading = ref(false)

let abortStream: (() => void) | null = null

// Knowledge Base state
const knowledgeBases = ref<RAGKnowledgeBase[]>([])
const kbDialogVisible = ref(false)
const deleteDialogVisible = ref(false)
const kbSaving = ref(false)
const editingKB = ref<RAGKnowledgeBase | null>(null)
const deletingKB = ref<RAGKnowledgeBase | null>(null)
const kbForm = ref({ name: '', description: '', namespace: '', filePath: '', collectionName: '' })
const folderInputRef = ref<HTMLInputElement>()
const fileInputRef = ref<HTMLInputElement>()
const uploadedFileCount = ref(0)
const uploadingFiles = ref(false)
const indexingStatus = ref('')  // '' | 'indexing' | 'done' | 'failed'

// Right sidebar tab state
const rightTab = ref<'kb' | 'plan'>('kb')

// Plan state
const currentPlan = ref<Plan | null>(null)

const isAdmin = computed(() => authStore.userInfo?.isAdmin === 1)

const loadKnowledgeBases = async () => {
  try {
    const res = await getRAGListApi()
    if (res.success) {
      knowledgeBases.value = (res.data || []) as RAGKnowledgeBase[]
    }
  } catch (e) {
    console.error('Failed to load knowledge bases:', e)
  }
}

const editKB = (kb: RAGKnowledgeBase) => {
  editingKB.value = kb
  kbForm.value = {
    name: kb.name,
    description: kb.description || '',
    namespace: kb.namespace,
    filePath: kb.filePath || '',
    collectionName: kb.collectionName || '',
  }
  uploadedFileCount.value = 0
  kbDialogVisible.value = true
}

const showAddDialogFn = () => {
  editingKB.value = null
  kbForm.value = { name: '', description: '', namespace: '', filePath: '', collectionName: '' }
  uploadedFileCount.value = 0
  indexingStatus.value = ''
  kbDialogVisible.value = true
}

const handleFileSelect = async (e: Event) => {
  const input = e.target as HTMLInputElement
  const fileList = input.files
  if (!fileList || fileList.length === 0) return

  const namespace = kbForm.value.namespace
  if (!namespace) {
    ElMessage.warning('请先填写命名空间')
    return
  }

  uploadingFiles.value = true
  indexingStatus.value = 'indexing'
  try {
    const collectionName = `rag_${namespace}`
    kbForm.value.collectionName = collectionName

    const res = await uploadRAGFilesApi(
      namespace,
      collectionName,
      Array.from(fileList)
    )
    if (!res.success) {
      indexingStatus.value = 'failed'
      ElMessage.error('上传失败')
      return
    }

    uploadedFileCount.value = res.fileCount
    kbForm.value.filePath = `./knowledge_base/${namespace}`
    ElMessage.success(res.message)

    // 轮询等待索引完成
    const AGENT_BASE_URL = import.meta.env.VITE_AGENT_BASE_URL || 'http://localhost:8000'
    await new Promise<void>((resolve, reject) => {
      const TIMEOUT = 5 * 60 * 1000 // 5 分钟超时
      const startTime = Date.now()
      const poll = setInterval(async () => {
        try {
          if (Date.now() - startTime > TIMEOUT) {
            clearInterval(poll)
            reject(new Error('索引超时'))
            return
          }
          const resp = await fetch(`${AGENT_BASE_URL}/api/agent/rag/index_status/${namespace}`)
          const data = await resp.json()
          if (data.status === 'done') {
            clearInterval(poll)
            resolve()
          } else if (data.status === 'failed' || data.status === 'idle') {
            clearInterval(poll)
            reject(new Error(data.error || (data.status === 'idle' ? '知识库管道不存在' : '索引失败')))
          }
        } catch {
          // 轮询失败忽略，下次继续
        }
      }, 2000)
    })

    indexingStatus.value = 'done'
    ElMessage.success('文件索引完成，请点击底部「保存」按钮创建知识库')
  } catch (e) {
    indexingStatus.value = 'failed'
    ElMessage.error('操作失败：' + (e as Error).message)
  } finally {
    uploadingFiles.value = false
    // 重置两个 input 以便重复选择
    if (folderInputRef.value) folderInputRef.value.value = ''
    if (fileInputRef.value) fileInputRef.value.value = ''
  }
}

const handleSaveKB = async () => {
  if (!kbForm.value.name || !kbForm.value.namespace) {
    ElMessage.warning('名称和命名空间为必填项')
    return
  }
  kbSaving.value = true
  try {
    if (editingKB.value) {
      const res = await updateRAGApi({
        ragId: editingKB.value.ragId,
        name: kbForm.value.name,
        description: kbForm.value.description,
        namespace: kbForm.value.namespace,
        filePath: kbForm.value.filePath,
        status: 1,
      } as RAGKnowledgeBase)
      if (res.success) ElMessage.success('更新成功')
    } else {
      if (!kbForm.value.filePath) {
        ElMessage.warning('请先上传文件并等待索引完成')
        return
      }
      const res = await addRAGApi({
        name: kbForm.value.name,
        description: kbForm.value.description,
        namespace: kbForm.value.namespace,
        collectionName: kbForm.value.collectionName,
        filePath: kbForm.value.filePath,
        fileCount: uploadedFileCount.value,
        status: 1,
      } as RAGKnowledgeBase)
      if (res.success) {
        ElMessage.success('创建成功')
      } else {
        ElMessage.error('保存失败：' + (res.errorMsg || '未知错误'))
        kbSaving.value = false
        return
      }
    }
    kbDialogVisible.value = false
    await loadKnowledgeBases()
  } catch (e) {
    ElMessage.error('操作失败：' + (e as Error).message)
  } finally {
    kbSaving.value = false
    editingKB.value = null
  }
}

const handleDeleteKB = (kb: RAGKnowledgeBase) => {
  deletingKB.value = kb
  deleteDialogVisible.value = true
}

const handleConfirmDelete = async () => {
  if (!deletingKB.value?.ragId) return
  kbSaving.value = true
  try {
    const res = await deleteRAGApi(deletingKB.value.ragId)
    if (res.success) {
      ElMessage.success('删除成功')
    }
    deleteDialogVisible.value = false
    await loadKnowledgeBases()
  } catch (e) {
    ElMessage.error('删除失败')
  } finally {
    kbSaving.value = false
    deletingKB.value = null
  }
}

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

  // 确保用户信息已加载（防止页面刷新后 userInfo 尚未就绪）
  if (!authStore.userInfo && authStore.token) {
    try {
      await authStore.getUserInfo()
    } catch (e) {
      console.error('无法获取用户信息:', e)
    }
  }

  // Add user message
  addMessage('user', text)
  inputMessage.value = ''

  // Add placeholder assistant message
  addMessage('assistant', '', true)
  const msgIndex = messages.value.length - 1

  // Initialize reactData
  messages.value[msgIndex].reactData = { steps: [], finalAnswer: '' }
  messages.value[msgIndex].reactCollapsed = false

  // 只发送当前用户输入，对话历史由后端管理
  const request: ChatRequest = {
    sessionId: sessionId.value,
    messages: [{ role: 'user', content: text, timestamp: Date.now() }],
    userId: authStore.userInfo?.userId,
  }

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

        // plan 事件：更新任务计划面板
        if (type === 'plan') {
          handlePlanEvent(data)
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
        loadSessions()
      }
    )
}

const loadSessions = async () => {
  try {
    sessionsLoading.value = true
    const list = await listSessionsApi()
    sessions.value = list
  } catch (e) {
    console.error('加载历史会话失败:', e)
  } finally {
    sessionsLoading.value = false
  }
}

const handleSelectSession = async (session: SessionDTO) => {
  if (abortStream) {
    abortStream()
    abortStream = null
  }

  loading.value = true
  try {
    const msgs = await getSessionMessagesApi(session.sessionId)
    sessionId.value = session.sessionId
    const baseTime = session.createdAt || Date.now()
    const formattedMessages: Message[] = msgs.map((msg: any, idx: number) => ({
      role: msg.role || 'user',
      content: msg.content || '',
      timestamp: msg.timestamp
        ? new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        : new Date(baseTime + idx * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      memories: [],
      memoriesCollapsed: true,
    }))
    messages.value = formattedMessages
    await loadPlan()
  } catch (e) {
    console.error('加载会话消息失败:', e)
    ElMessage.error('加载历史消息失败')
  } finally {
    loading.value = false
  }
  scrollToBottom()
}

const handleDeleteSession = async (session: SessionDTO) => {
  try {
    await deleteSessionApi(session.sessionId)
    ElMessage.success('对话已删除')
    if (session.sessionId === sessionId.value) {
      messages.value = []
      await initNewSession()
    }
    await loadSessions()
  } catch (e) {
    console.error('删除会话失败:', e)
    ElMessage.error('删除失败')
  }
}

const handleRenameSession = async (sessionId: string, title: string) => {
  try {
    await updateSessionTitleApi(sessionId, title)
    await loadSessions()
  } catch (e) {
    console.error('重命名会话失败:', e)
    ElMessage.error('重命名失败')
  }
}

const handleNewChat = async () => {
  if (abortStream) {
    abortStream()
    abortStream = null
  }
  messages.value = []
  currentPlan.value = null
  loading.value = false
  await initNewSession()
  scrollToBottom()
}

const initNewSession = async () => {
  try {
    const newSessionId = await initSessionApi()
    sessionId.value = newSessionId
    await loadSessions()
  } catch (e) {
    console.error('初始化 session 失败:', e)
  }
}

const handleClearChat = async () => {
  await handleNewChat()
}

const handlePlanEvent = (eventData: any) => {
  if (!eventData || !eventData.type) return
  const { type, data } = eventData

  if (type === 'plan_init' && data) {
    // Full plan DTO
    currentPlan.value = data as Plan
  } else if (type === 'plan_task_added' && data) {
    // Parent task was updated with new subtask
    if (currentPlan.value?.rootTask) {
      updateTaskInTree(currentPlan.value.rootTask, data as any)
    }
  } else if (type === 'plan_task_update' && data) {
    // Task state updated
    if (currentPlan.value?.rootTask) {
      updateTaskInTree(currentPlan.value.rootTask, data as any)
    }
  }
}

const updateTaskInTree = (node: any, updatedTask: any) => {
  if (node.taskPath === updatedTask.taskPath) {
    node.taskState = updatedTask.taskState
    node.subtasks = updatedTask.subtasks || []
    return true
  }
  for (const sub of node.subtasks || []) {
    if (updateTaskInTree(sub, updatedTask)) return true
  }
  return false
}

const loadPlan = async () => {
  if (!sessionId.value) {
    currentPlan.value = null
    return
  }
  try {
    const res = await getPlanBySessionApi(sessionId.value)
    if (res.success && res.data) {
      currentPlan.value = res.data as Plan
    } else {
      currentPlan.value = null
    }
  } catch {
    currentPlan.value = null
  }
}

const handleLogout = () => {
  localStorage.removeItem('token')
  ElMessage.success('Logged out successfully')
  router.push('/login')
}

onMounted(async () => {
  await initNewSession()
  loadKnowledgeBases()
})

// 用户切换时重新初始化 session
watch(() => authStore.userInfo?.userId, async () => {
  messages.value = []
  loading.value = false
  await initNewSession()
})
</script>

<style scoped>
/* Custom scrollbar */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
  border-radius: 3px;
}
::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;
  transition: background 0.2s;
}
::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}

/* Message fade-in animation */
:deep(.animate-fadeIn) {
  animation: fadeInUp 0.3s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Chat input styling */
:deep(.chat-input .el-textarea__inner) {
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  padding: 10px 14px;
  font-size: 14px;
  line-height: 1.5;
  transition: border-color 0.2s, box-shadow 0.2s;
  background: #f9fafb;
  resize: none;
}

:deep(.chat-input .el-textarea__inner:focus) {
  border-color: #818cf8;
  box-shadow: 0 0 0 3px rgba(129, 140, 248, 0.1);
  background: white;
}

/* Send button styling */
.send-btn {
  height: 42px !important;
  width: 42px !important;
  padding: 0 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  border-radius: 50% !important;
  background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
  border: none !important;
  transition: all 0.2s ease !important;
}

.send-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4) !important;
}

.send-btn:active {
  transform: scale(0.95);
}

/* Markdown body refinements */
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
