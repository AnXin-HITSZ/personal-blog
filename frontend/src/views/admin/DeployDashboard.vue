<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import type { DeploymentSummary, DeploymentDetail, PhaseInfo, LogEntry } from '@/types'
import {
  triggerDeployApi,
  getDeployHistoryApi,
  getDeployDetailApi,
  cancelDeployApi,
} from '@/api/deployment'

// ─── 状态 ───
const loading = ref(true)
const error = ref(false)
const deployments = ref<DeploymentSummary[]>([])
const total = ref(0)
const page = ref(1)

// 活跃部署
const activeDeploymentId = ref<string | null>(null)
const activeDetail = ref<DeploymentDetail | null>(null)
const pollingTimer = ref<ReturnType<typeof setInterval> | null>(null)

// 触发弹窗
const showTriggerModal = ref(false)
const deployBranch = ref('main')
const triggering = ref(false)

// 详情抽屉
const showDetailDrawer = ref(false)
const selectedDeployment = ref<DeploymentSummary | null>(null)
const selectedDetail = ref<DeploymentDetail | null>(null)
const detailLoading = ref(false)

const router = useRouter()

// ─── 计算属性 ───
const phaseStatusColor = (status: string) => {
  const map: Record<string, string> = {
    pending: 'info',
    running: 'warning',
    success: 'success',
    failed: 'danger',
    skipped: 'info',
  }
  return map[status] || 'info'
}

const statusLabel = (status: string) => {
  const map: Record<string, string> = {
    running: '运行中',
    success: '成功',
    failed: '失败',
    rolled_back: '已回滚',
    cancelled: '已取消',
  }
  return map[status] || status
}

const statusType = (status: string) => {
  const map: Record<string, string> = {
    running: 'warning',
    success: 'success',
    failed: 'danger',
    rolled_back: 'warning',
    cancelled: 'info',
  }
  return map[status] || 'info'
}

const isRunning = computed(() => activeDeploymentId.value !== null)

const stats = computed(() => {
  const total = deployments.value.length
  const success = deployments.value.filter((d) => d.final_status === 'success').length
  const failed = deployments.value.filter((d) => d.final_status === 'failed').length
  const latest = deployments.value[0]
  return { total, success, failed, latest }
})

// ─── 加载历史 ───
async function fetchHistory() {
  try {
    error.value = false
    const res = await getDeployHistoryApi(page.value)
    if (res.success) {
      const data = res.data as { deployments: DeploymentSummary[]; total: number }
      deployments.value = data?.deployments ?? []
      total.value = data?.total ?? 0

      // 检查是否有运行中的部署
      const running = deployments.value.find((d) => d.final_status === 'running')
      if (running) {
        activeDeploymentId.value = running.deployment_id
        startPolling(running.deployment_id)
      }
    } else {
      error.value = true
    }
  } catch {
    error.value = true
  } finally {
    loading.value = false
  }
}

// ─── 轮询活跃部署 ───
function startPolling(deployId: string) {
  stopPolling()
  activeDeploymentId.value = deployId
  pollingTimer.value = setInterval(async () => {
    try {
      const res = await getDeployDetailApi(deployId)
      if (res.success) {
        const detail = res.data as DeploymentDetail
        activeDetail.value = detail

        // 检查是否结束
        if (detail.final_status !== 'running') {
          stopPolling()
          activeDeploymentId.value = null
          ElMessage.success(`部署完成: ${statusLabel(detail.final_status)}`)
          await fetchHistory() // 刷新列表
        }
      }
    } catch {
      // 忽略轮询错误
    }
  }, 2000)
}

function stopPolling() {
  if (pollingTimer.value) {
    clearInterval(pollingTimer.value)
    pollingTimer.value = null
  }
}

// ─── 触发部署 ───
async function handleTrigger() {
  triggering.value = true
  try {
    const res = await triggerDeployApi(deployBranch.value || undefined)
    if (res.success) {
      ElMessage.success('部署已启动')
      showTriggerModal.value = false

      // 从响应获取 deployment_id 立即开始轮询
      const data = res.data as { deployment_id?: string }
      if (data?.deployment_id) {
        startPolling(data.deployment_id)
        const detailRes = await getDeployDetailApi(data.deployment_id)
        if (detailRes.success) {
          activeDetail.value = detailRes.data as DeploymentDetail
        }
      } else {
        // 降级：通过 history 查找 running 部署
        await fetchHistory()
        if (!activeDeploymentId.value) {
          let retries = 0
          const timer = setInterval(async () => {
            retries++
            await fetchHistory()
            if (activeDeploymentId.value || retries >= 10) {
              clearInterval(timer)
            }
          }, 1000)
        }
      }
    } else {
      ElMessage.error(res.errorMsg || '触发部署失败')
    }
  } catch {
    ElMessage.error('触发部署失败，请检查服务状态')
  } finally {
    triggering.value = false
  }
}

// ─── 取消部署 ───
async function handleCancel() {
  if (!activeDeploymentId.value) return
  try {
    await ElMessageBox.confirm('确定要取消当前部署吗？', '取消部署', {
      confirmButtonText: '取消部署',
      cancelButtonText: '不取消',
      type: 'warning',
    })
    await cancelDeployApi(activeDeploymentId.value)
    ElMessage.success('已取消部署')
    stopPolling()
    activeDeploymentId.value = null
    await fetchHistory()
  } catch {
    // 用户取消操作
  }
}

// ─── 查看详情 ───
async function showDetail(row: DeploymentSummary) {
  selectedDeployment.value = row
  showDetailDrawer.value = true
  detailLoading.value = true
  try {
    const res = await getDeployDetailApi(row.deployment_id)
    if (res.success) {
      selectedDetail.value = res.data as DeploymentDetail
    }
  } catch {
    ElMessage.error('加载详情失败')
  } finally {
    detailLoading.value = false
  }
}

// ─── 格式化 ───
function formatTime(iso: string): string {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN')
}

function formatDuration(ms: number): string {
  if (!ms) return '-'
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  const m = Math.floor(ms / 60000)
  const s = Math.floor((ms % 60000) / 1000)
  return `${m}m${s}s`
}

function trimHash(hash: string): string {
  return hash ? hash.slice(0, 8) : '-'
}

// ─── 生命周期 ───
onMounted(() => {
  fetchHistory()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<template>
  <div class="max-w-6xl mx-auto px-4 py-8">
    <!-- ═══ Header ═══ -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">部署管理</h1>
        <p class="text-sm text-gray-400 mt-1">CI/CD 自动化部署流水线</p>
      </div>
      <div class="flex items-center gap-2">
        <el-button
          v-if="isRunning"
          type="danger"
          plain
          @click="handleCancel"
        >
          <el-icon><Close /></el-icon>
          取消部署
        </el-button>
        <el-button
          type="primary"
          size="large"
          :disabled="isRunning"
          @click="showTriggerModal = true"
        >
          <el-icon><Upload /></el-icon>
          新建部署
        </el-button>
      </div>
    </div>

    <!-- ═══ 活跃部署横幅 ═══ -->
    <div
      v-if="isRunning && activeDetail"
      class="mb-8 bg-amber-50 border border-amber-200 rounded-xl p-6"
    >
      <div class="flex items-center gap-2 mb-4">
        <el-icon class="text-amber-500 text-lg animate-spin"><Loading /></el-icon>
        <span class="font-semibold text-amber-700">部署运行中</span>
        <el-tag size="small" type="warning">
          {{ activeDetail.current_phase }}
        </el-tag>
      </div>

      <!-- 阶段进度条 -->
      <div class="flex items-center gap-1 mb-4">
        <template v-for="(phase, i) in activeDetail.phases" :key="phase.name">
          <div
            class="flex items-center gap-1"
            :class="phase.status === 'running' ? 'text-amber-600' : phase.status === 'success' ? 'text-green-600' : phase.status === 'failed' ? 'text-red-600' : 'text-gray-400'"
          >
            <el-icon v-if="phase.status === 'success'" size="14"><Check /></el-icon>
            <el-icon v-else-if="phase.status === 'running'" size="14" class="animate-spin"><Loading /></el-icon>
            <el-icon v-else-if="phase.status === 'failed'" size="14"><Close /></el-icon>
            <el-icon v-else size="14"><Circle /></el-icon>
            <span class="text-xs whitespace-nowrap">{{ phase.label }}</span>
          </div>
          <el-icon
            v-if="i < activeDetail.phases.length - 1"
            size="12"
            class="text-gray-300 mx-1"
          >
            <ArrowRight />
          </el-icon>
        </template>
      </div>

      <!-- 实时日志 -->
      <div class="bg-gray-900 text-green-400 rounded-lg p-4 font-mono text-xs max-h-40 overflow-y-auto">
        <div v-if="activeDetail.logs.length === 0" class="text-gray-500">
          等待日志输出...
        </div>
        <div v-for="(log, i) in activeDetail.logs" :key="i" class="leading-relaxed">
          <span class="text-gray-500">[{{ log.phase }}]</span> {{ log.message }}
        </div>
      </div>
    </div>

    <!-- ═══ 统计卡片 ═══ -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
      <div class="bg-white rounded-xl border border-gray-100 p-5">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-500">
            <el-icon class="text-xl"><Connection /></el-icon>
          </div>
          <div>
            <p class="text-xs text-gray-400">总部署次数</p>
            <p class="text-xl font-bold text-gray-800">{{ stats.total }}</p>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-xl border border-gray-100 p-5">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center text-green-500">
            <el-icon class="text-xl"><Check /></el-icon>
          </div>
          <div>
            <p class="text-xs text-gray-400">成功</p>
            <p class="text-xl font-bold text-gray-800">{{ stats.success }}</p>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-xl border border-gray-100 p-5">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-red-50 flex items-center justify-center text-red-500">
            <el-icon class="text-xl"><Close /></el-icon>
          </div>
          <div>
            <p class="text-xs text-gray-400">失败</p>
            <p class="text-xl font-bold text-gray-800">{{ stats.failed }}</p>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-xl border border-gray-100 p-5">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-amber-50 flex items-center justify-center text-amber-500">
            <el-icon class="text-xl"><Clock /></el-icon>
          </div>
          <div>
            <p class="text-xs text-gray-400">最近部署</p>
            <p class="text-sm font-medium text-gray-800 truncate">
              {{ stats.latest ? trimHash(stats.latest.commit_hash) : '-' }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ 部署历史表格 ═══ -->
    <div class="bg-white rounded-xl border border-gray-100 overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-50">
        <h2 class="font-semibold text-gray-700">部署历史</h2>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="p-8 text-center">
        <el-icon class="text-2xl text-gray-300 animate-spin"><Loading /></el-icon>
        <p class="mt-2 text-sm text-gray-400">加载中...</p>
      </div>

      <!-- 错误状态 -->
      <div v-else-if="error" class="p-8 text-center">
        <el-icon class="text-4xl text-red-200"><WarningFilled /></el-icon>
        <p class="mt-2 text-sm text-gray-500">加载失败，请检查服务状态</p>
        <el-button class="mt-4" size="small" @click="fetchHistory">
          重试
        </el-button>
      </div>

      <!-- 空状态 -->
      <div v-else-if="deployments.length === 0" class="p-8 text-center">
        <el-icon class="text-4xl text-gray-200"><Upload /></el-icon>
        <p class="mt-2 text-sm text-gray-400">还没有部署记录</p>
        <el-button class="mt-4" size="small" type="primary" @click="showTriggerModal = true">
          新建部署
        </el-button>
      </div>

      <!-- 表格 -->
      <el-table
        v-else
        :data="deployments"
        stripe
        empty-text="暂无数据"
        style="width: 100%"
        @row-click="showDetail"
      >
        <el-table-column label="ID" width="200">
          <template #default="{ row }">
            <span class="text-sm text-gray-600 font-mono">{{ trimHash(row.deployment_id) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="触发方式" width="100">
          <template #default="{ row }">
            <el-tag :type="row.trigger_type === 'webhook' ? 'success' : 'primary'" size="small">
              {{ row.trigger_type === 'webhook' ? 'Webhook' : '手动' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="提交" width="130">
          <template #default="{ row }">
            <span class="font-mono text-sm text-gray-600">{{ trimHash(row.commit_hash) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="提交信息" min-width="200">
          <template #default="{ row }">
            <span class="text-sm text-gray-600 truncate">{{ row.commit_message || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.final_status)" size="small" effect="dark">
              {{ statusLabel(row.final_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="耗时" width="80">
          <template #default="{ row }">
            <span class="text-sm text-gray-400">{{ formatDuration(row.duration_ms) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="时间" width="170">
          <template #default="{ row }">
            <span class="text-sm text-gray-400">{{ formatTime(row.created_at) }}</span>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div v-if="total > 20" class="px-6 py-4 border-t border-gray-50 flex justify-center">
        <el-pagination
          v-model:current-page="page.value"
          :page-size="20"
          :total="total"
          layout="prev, pager, next"
          @current-change="fetchHistory"
        />
      </div>
    </div>

    <!-- ═══ 触发部署弹窗 ═══ -->
    <el-dialog
      v-model="showTriggerModal"
      title="新建部署"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-form label-width="80px">
        <el-form-item label="目标分支">
          <el-input v-model="deployBranch" placeholder="main" :disabled="triggering" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showTriggerModal = false" :disabled="triggering">取消</el-button>
        <el-button type="primary" :loading="triggering" @click="handleTrigger">
          {{ triggering ? '启动中...' : '开始部署' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- ═══ 部署详情抽屉 ═══ -->
    <el-drawer
      v-model="showDetailDrawer"
      title="部署详情"
      size="50%"
      :close-on-click-modal="false"
    >
      <div v-if="detailLoading" class="text-center py-8">
        <el-icon class="text-2xl text-gray-300 animate-spin"><Loading /></el-icon>
        <p class="mt-2 text-sm text-gray-400">加载中...</p>
      </div>

      <template v-else-if="selectedDetail">
        <div class="space-y-6">
          <!-- 基本信息 -->
          <div class="bg-gray-50 rounded-lg p-4">
            <h3 class="font-semibold text-gray-700 mb-3">基本信息</h3>
            <el-descriptions :column="2" size="small" border>
              <el-descriptions-item label="部署 ID">
                <span class="font-mono text-xs">{{ selectedDetail.deployment_id }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="触发方式">
                <el-tag size="small" :type="selectedDetail.trigger_type === 'webhook' ? 'success' : 'primary'">
                  {{ selectedDetail.trigger_type === 'webhook' ? 'Webhook' : '手动' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="提交哈希">
                <span class="font-mono text-xs">{{ selectedDetail.commit_hash || '-' }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="回滚目标">
                <span class="font-mono text-xs">{{ selectedDetail.previous_commit_hash || '-' }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="提交信息" :span="2">
                {{ selectedDetail.commit_message || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="最终状态">
                <el-tag :type="statusType(selectedDetail.final_status)" size="small" effect="dark">
                  {{ statusLabel(selectedDetail.final_status) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="创建时间">
                {{ formatTime(selectedDetail.created_at) }}
              </el-descriptions-item>
            </el-descriptions>
          </div>

          <!-- 阶段列表 -->
          <div class="bg-gray-50 rounded-lg p-4">
            <h3 class="font-semibold text-gray-700 mb-3">阶段状态</h3>
            <el-timeline>
              <el-timeline-item
                v-for="phase in selectedDetail.phases"
                :key="phase.name"
                :type="phaseStatusColor(phase.status) as any"
                :hollow="phase.status === 'pending'"
              >
                <div class="flex items-center gap-2">
                  <span class="font-medium text-sm">{{ phase.label }}</span>
                  <el-tag :type="phaseStatusColor(phase.status)" size="small" effect="plain">
                    {{ phase.status }}
                  </el-tag>
                </div>
              </el-timeline-item>
            </el-timeline>
          </div>

          <!-- 完整日志 -->
          <div class="bg-gray-50 rounded-lg p-4">
            <h3 class="font-semibold text-gray-700 mb-3">部署日志</h3>
            <div
              v-if="selectedDetail.logs.length === 0"
              class="text-sm text-gray-400 text-center py-4"
            >
              暂无日志
            </div>
            <div
              v-else
              class="bg-gray-900 text-green-400 rounded-lg p-4 font-mono text-xs max-h-60 overflow-y-auto"
            >
              <div v-for="(log, i) in selectedDetail.logs" :key="i" class="leading-relaxed">
                <span class="text-gray-500">[{{ log.timestamp?.slice(11, 19) }}]</span>
                <span class="text-gray-400 ml-1">[{{ log.phase }}]</span>
                {{ log.message }}
              </div>
            </div>
          </div>

          <!-- 错误信息 -->
          <div v-if="selectedDetail.error" class="bg-red-50 border border-red-200 rounded-lg p-4">
            <h3 class="font-semibold text-red-700 mb-2">错误信息</h3>
            <pre class="text-sm text-red-600 whitespace-pre-wrap">{{ selectedDetail.error }}</pre>
          </div>
        </div>
      </template>
    </el-drawer>
  </div>
</template>
