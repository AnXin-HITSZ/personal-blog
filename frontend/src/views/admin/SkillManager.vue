<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getSkillsApi, configureSkillsApi } from '@/api/agent'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Switch } from '@element-plus/icons-vue'

interface SkillInfo {
  name: string
  description: string
  tool_count: number
  enabled_by_default: boolean
}

const loading = ref(true)
const saving = ref(false)
const skills = ref<SkillInfo[]>([])
const enabledNames = ref<string[]>([])
const originalEnabled = ref<string[]>([])

const hasChanges = ref(false)

onMounted(async () => {
  await fetchSkills()
})

async function fetchSkills() {
  loading.value = true
  try {
    const res = await getSkillsApi()
    // Spring Boot 代理包装: { success, data: { code, message, data: { skills, enabled } } }
    if (res.success && res.data) {
      const fastapiData = res.data
      if (fastapiData.code === 200 && fastapiData.data) {
        skills.value = fastapiData.data.skills ?? []
        enabledNames.value = [...(fastapiData.data.enabled ?? [])]
        originalEnabled.value = [...enabledNames.value]
      }
    }
  } catch {
    // Error already handled by axios interceptor (including 401 redirect)
  } finally {
    loading.value = false
  }
}

function isEnabled(name: string): boolean {
  return enabledNames.value.includes(name)
}

function toggleSkill(name: string, enabled: boolean) {
  if (enabled) {
    if (!enabledNames.value.includes(name)) {
      enabledNames.value.push(name)
    }
  } else {
    enabledNames.value = enabledNames.value.filter((n) => n !== name)
  }
  hasChanges.value =
    enabledNames.value.length !== originalEnabled.value.length ||
    !enabledNames.value.every((n) => originalEnabled.value.includes(n))
}

async function handleSave() {
  saving.value = true
  try {
    const res = await configureSkillsApi(enabledNames.value)
    // Spring Boot 代理包装: { success, data: { code, message, data } }
    if (res.success && res.data?.code === 200) {
      ElMessage.success('Skill 配置已更新，将在下一轮对话生效')
      originalEnabled.value = [...enabledNames.value]
      hasChanges.value = false
    } else {
      ElMessage.error(res.data?.message || res.errorMsg || '保存失败')
    }
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function handleReset() {
  await ElMessageBox.confirm('重置为默认配置？', '提示', {
    type: 'info',
    confirmButtonText: '重置',
    cancelButtonText: '取消',
  })
  // 设置为默认启用的 skill
  const defaults = skills.value.filter((s) => s.enabled_by_default).map((s) => s.name)
  enabledNames.value = defaults
  hasChanges.value = true
}
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 py-8">
    <!-- Page header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">AI 能力管理</h1>
        <p class="text-sm text-gray-400 mt-1">
          启用的能力将注入到 Agent 的 System Prompt 和工具列表中，禁用后下一轮对话生效
        </p>
      </div>
      <div class="flex gap-2">
        <el-button :disabled="!hasChanges" @click="handleReset">重置默认</el-button>
        <el-button type="primary" :loading="saving" :disabled="!hasChanges" @click="handleSave">
          保存配置
        </el-button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-16 text-gray-400">
      <el-icon class="text-3xl animate-spin"><Loading /></el-icon>
      <p class="mt-3 text-sm">加载中...</p>
    </div>

    <!-- Skill cards -->
    <div v-else class="space-y-4">
      <div
        v-for="skill in skills"
        :key="skill.name"
        class="bg-white rounded-xl border border-gray-100 p-5 transition-shadow hover:shadow-sm"
      >
        <div class="flex items-center justify-between">
          <div class="flex items-start gap-4">
            <!-- Icon -->
            <div
              class="w-10 h-10 rounded-lg flex items-center justify-center text-lg shrink-0"
              :class="isEnabled(skill.name)
                ? 'bg-indigo-50 text-indigo-500'
                : 'bg-gray-50 text-gray-300'"
            >
              <template v-if="skill.name === 'rag'">🧠</template>
              <template v-else-if="skill.name === 'time'">⏰</template>
              <template v-else-if="skill.name === 'mcp'">🔌</template>
              <template v-else>🧩</template>
            </div>
            <!-- Info -->
            <div>
              <div class="flex items-center gap-2">
                <h3 class="font-semibold text-gray-800">{{ skill.name }}</h3>
                <span
                  class="text-xs text-gray-400 bg-gray-50 px-2 py-0.5 rounded"
                >
                  {{ skill.tool_count }} 个工具
                </span>
                <span
                  v-if="skill.enabled_by_default"
                  class="text-xs text-amber-500 bg-amber-50 px-2 py-0.5 rounded"
                >
                  默认启用
                </span>
              </div>
              <p class="text-sm text-gray-400 mt-1">{{ skill.description }}</p>
            </div>
          </div>
          <!-- Toggle -->
          <el-switch
            :model-value="isEnabled(skill.name)"
            @update:model-value="(val: boolean) => toggleSkill(skill.name, val)"
            active-text="启用"
            inactive-text="禁用"
          />
        </div>
      </div>

      <!-- Empty state -->
      <div v-if="skills.length === 0" class="text-center py-16 text-gray-400">
        <p>暂无可用 Skill</p>
      </div>
    </div>
  </div>
</template>
